import cv2, numpy as np, math, os

path = r"D:\project\Know-Your-Gpa\测试集\occluded-sample.jpg"
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Detect blue polygon
s_min = 145
mask = cv2.inRange(hsv, np.array([85, s_min, 40]), np.array([160, 255, 255]))
k = np.ones((2,2), np.uint8)
mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)
contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

target_y = h * 0.3
best = None; best_dist = 99999
for i, cnt in enumerate(contours):
    if hierarchy[0][i][3] != -1: continue
    area = cv2.contourArea(cnt)
    if area < 5000 or area > w*h*0.5: continue
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.015*peri, True)
    nv = len(approx)
    if nv < 7 or nv > 20: continue
    ctr = np.mean(approx.reshape(-1,2), axis=0)
    d = abs(ctr[1] - target_y)
    if d < best_dist: best_dist = d; best = (cnt, approx, nv, ctr)

cnt, approx, nv, center = best
peri = cv2.arcLength(cnt, True)
approx = cv2.approxPolyDP(cnt, 0.01*peri, True)
verts = approx.reshape(-1, 2).astype(np.float64)
margin = 5
inner_verts = np.array([v for v in verts
    if margin < v[0] < w-margin and margin < v[1] < h-margin])
center = np.mean(inner_verts, axis=0)
N = len(inner_verts)
slice_angle = math.pi / N

# Score distances via radial scan
axis_dists = []
for i in range(N):
    angle = slice_angle * i * 2
    found_d = 0
    for d in range(5, int(min(w,h)), 1):
        px = int(center[0] + d * math.cos(angle))
        py = int(center[1] + d * math.sin(angle))
        if px < 1 or px >= w-1 or py < 1 or py >= h-1: break
        if mask[py, px] > 0:
            found_d = d
        elif found_d > 0:
            break
    axis_dists.append(float(found_d))

inner_r = max(axis_dists)
V_channel = hsv[:,:,2]

# Credit distances: scan along sector midpoints using V (brightness)
# Credit polygon has V ~200-240, background gray has V ~180
credit_dists = []
for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    # First, find a reliable reference V inside the credit polygon
    ref_r = inner_r * 0.6
    ref_px = int(center[0] + ref_r * math.cos(mid_angle))
    ref_py = int(center[1] + ref_r * math.sin(mid_angle))
    ref_V = V_channel[ref_py, ref_px] if ref_px >= 0 and ref_px < w and ref_py >= 0 and ref_py < h else 200
    
    # Scan outward, find where V drops significantly (credit polygon ends)
    found_d = 0
    for d in range(int(inner_r * 0.5), int(inner_r * 3), 2):
        px = int(center[0] + d * math.cos(mid_angle))
        py = int(center[1] + d * math.sin(mid_angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        curr_V = V_channel[py, px]
        if curr_V < ref_V - 15:  # Significant brightness drop
            found_d = d
            break
        ref_V = 0.7 * ref_V + 0.3 * curr_V  # adaptive reference
    credit_dists.append(float(found_d) if found_d > 0 else float(inner_r * 2))

max_cred_d = max(credit_dists)
credit_ratios = [d / max_cred_d for d in credit_dists]

# Also get TERM_B credits for comparison
cred_TERM_B = [4, 3, 1, 4, 2, 2, 1, 1, 3, 1, 2, 5, 3, 2, 1, 1]
total_TERM_B = sum(cred_TERM_B)  # 36
total_test1 = total_TERM_B + 2  # 38

# Normalize TERM_B credits to 8 by summing adjacent pairs
cred_TERM_B_8 = [cred_TERM_B[i*2] + cred_TERM_B[i*2+1] for i in range(8)]
# [4+3, 1+4, 2+2, 1+1, 3+1, 2+5, 3+2, 1+1] = [7, 5, 4, 2, 4, 7, 5, 2] = 36
# +2 total = 38, need to distribute

print("N={} center=({:.0f},{:.0f}) inner_r={:.0f}".format(N, center[0], center[1], inner_r))
print()
print("{:>8s}  {:>6s}  {:>7s}  {:>7s}  {:>7s}  {:>7s}".format(
    "Angle", "AxisD", "Score", "CredD", "Cred%", "CredEst"))
print("-" * 60)
for i in range(N):
    angle = slice_angle * i * 2
    score = (axis_dists[i] / inner_r) ** 0.25 * 100 if inner_r > 0 else 0
    cred_pct = credit_ratios[i] * 100
    cred_est = credit_ratios[i] * total_test1
    print("{:>8.1f}  {:>6.0f}  {:>7.2f}  {:>7.0f}  {:>7.1f}  {:>7.1f}".format(
        math.degrees(angle), axis_dists[i], score, credit_dists[i], cred_pct, cred_est))

print()
print("TERM_B credits (paired): {}".format(cred_TERM_B_8))
print("occluded-sample estimated credits: {}".format([round(credit_ratios[i] * total_test1, 1) for i in range(N)]))
