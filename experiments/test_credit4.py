import cv2, numpy as np, math, os

path = r"D:\project\Know-Your-Gpa\测试集\occluded-sample.jpg"
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
S = hsv[:,:,1]
V = hsv[:,:,2]

# Parameters from detection
center = np.array([297.0, 640.0])
N = 8
slice_angle = math.pi / N
inner_r = 94
outer_r = inner_r * 1.5  # from Flutter: outer = inner * 3/2

# Credit polygon detection: scan along sector midpoints
# The credit polygon has S > some threshold (typically 5-15)
# Background has S = 0 with V = 181
print("Credit polygon detection via S channel:")
print("outer_r = {:.0f}".format(outer_r))
print()
print("{:>8s}  {:>6s}  {:>8s}  {:>8s}  {:>8s}".format(
    "Sector", "CredR", "Sat", "V", "Credit%"))
print("-" * 50)

credit_dists = []
for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    
    # Scan outward, find where S consistently drops below threshold
    found_edge = 0
    low_s_count = 0
    for d in range(10, int(outer_r * 2.5), 2):
        px = int(center[0] + d * math.cos(mid_angle))
        py = int(center[1] + d * math.sin(mid_angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        
        s_val = int(S[py, px])
        v_val = int(V[py, px])
        
        if s_val < 5:
            low_s_count += 1
            if low_s_count >= 3 and found_edge == 0:  # 3 consecutive low-S pixels
                found_edge = d
        else:
            low_s_count = 0
    
    credit_dists.append(float(found_edge) if found_edge > 0 else float(outer_r))
    
    # Sample at the found edge position
    if found_edge > 0:
        px = int(center[0] + found_edge * math.cos(mid_angle))
        py = int(center[1] + found_edge * math.sin(mid_angle))
        s_edge = int(S[py, px])
        v_edge = int(V[py, px])
    else:
        s_edge = -1; v_edge = -1
    
    credit_pct = credit_dists[-1] / outer_r * 100 if outer_r > 0 else 0
    print("{:>8d}  {:>6.0f}  {:>8d}  {:>8d}  {:>7.1f}%".format(
        i, credit_dists[-1], s_edge, v_edge, credit_pct))

# Now detect credit polygon for sem1 and sem2 too (for validation)
print()
print("=== Validating on TERM_A (sem1) ===")
for sem_path in [r"D:\project\Know-Your-Gpa\测试集\SYNTHETIC_TERM_1.jpg",
                 r"D:\project\Know-Your-Gpa\测试集\SYNTHETIC_TERM_2.jpg"]:
    with open(sem_path, "rb") as fp: raw = fp.read()
    img2 = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    h2, w2 = img2.shape[:2]
    hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
    S2 = hsv2[:,:,1]; V2 = hsv2[:,:,2]
    
    # Quick center estimate from blue polygon
    s_min = 155 if "TERM_A" in sem_path else 150
    mask2 = cv2.inRange(hsv2, np.array([90, s_min, 50]), np.array([150, 255, 255]))
    k = np.ones((2,2), np.uint8)
    mask2 = cv2.dilate(mask2, k, 1); mask2 = cv2.erode(mask2, k, 1)
    contours2, hierarchy2 = cv2.findContours(mask2, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    best2 = None; best_area2 = 0
    for j, cnt2 in enumerate(contours2):
        if hierarchy2[0][j][3] != -1: continue
        area2 = cv2.contourArea(cnt2)
        if area2 > w2*h2*0.95: continue
        if area2 > best_area2: best_area2 = area2; best2 = cnt2
    
    if best2 is None: continue
    peri2 = cv2.arcLength(best2, True)
    approx2 = cv2.approxPolyDP(best2, 0.015*peri2, True)
    verts2 = approx2.reshape(-1, 2).astype(np.float64)
    margin2 = 5
    inner_verts2 = np.array([v for v in verts2
        if margin2 < v[0] < w2-margin2 and margin2 < v[1] < h2-margin2])
    if len(inner_verts2) < 3: continue
    ctr2 = np.mean(inner_verts2, axis=0)
    
    # Get inner_r via radial scan
    N2 = len(inner_verts2)
    sl2 = math.pi / N2
    axis_d2 = []
    for i2 in range(N2):
        a2 = sl2 * i2 * 2
        fd = 0
        for d2 in range(5, int(min(w2,h2)), 1):
            px2 = int(ctr2[0] + d2 * math.cos(a2))
            py2 = int(ctr2[1] + d2 * math.sin(a2))
            if px2 < 1 or px2 >= w2-1 or py2 < 1 or py2 >= h2-1: break
            if mask2[py2, px2] > 0:
                fd = d2
            elif fd > 0: break
        axis_d2.append(float(fd))
    inr2 = max(axis_d2) if axis_d2 else 100
    outr2 = inr2 * 1.5
    
    # Credit detection per sector
    cred_d2 = []
    for i2 in range(N2):
        ma2 = sl2 * (i2 * 2 + 1)
        edge = 0; low_c = 0
        for d2 in range(10, int(outr2 * 2.5), 2):
            px2 = int(ctr2[0] + d2 * math.cos(ma2))
            py2 = int(ctr2[1] + d2 * math.sin(ma2))
            if px2 < 2 or px2 >= w2-2 or py2 < 2 or py2 >= h2-2: break
            if int(S2[py2, px2]) < 5:
                low_c += 1
                if low_c >= 3 and edge == 0: edge = d2
            else:
                low_c = 0
        cred_d2.append(float(edge) if edge > 0 else float(outr2))
    
    fname = os.path.basename(sem_path)
    print("{}: N={} inr={:.0f} outr={:.0f}".format(fname, N2, inr2, outr2))
    print("  credit_dists: {}".format([round(d,0) for d in cred_d2]))
    print("  credit_ratios: {}".format([round(d/outr2, 2) if outr2>0 else 0 for d in cred_d2]))
