import cv2, numpy as np, math, os

path = r"D:\project\Know-Your-Gpa\测试集\occluded-sample.jpg"
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Use same detection: S>145 for blue polygon
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

# Radial scan along axes (score polygon)
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

# Now detect credit polygon - scan in each SECTOR (between axes)
# The credit polygon fans span from the midpoint between axes
# Fan for course i spans from angle (i-0.5)*2*slice to (i+0.5)*2*slice
# The credit polygon extends to outer * credit_ratio
# Let's scan radially at the sector midpoint
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

credit_dists = []
for i in range(N):
    # Sector midpoint angle
    mid_angle = slice_angle * (i * 2 + 1)  # between axis i and axis i+1
    # Scan outward and look for credit polygon edge
    # The credit polygon is a filled gray region
    # Look for transition from filled to background
    prev_val = gray[int(center[1]), int(center[0])]
    found_d = 0
    for d in range(10, int(min(w,h)*0.4), 2):
        px = int(center[0] + d * math.cos(mid_angle))
        py = int(center[1] + d * math.sin(mid_angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        curr_val = gray[py, px]
        # Look for significant brightness change
        if abs(curr_val - prev_val) > 20:
            found_d = d
            break
        prev_val = curr_val
    credit_dists.append(float(found_d) if found_d > 0 else 0.0)

# Normalize credit ratios
max_credit_d = max(credit_dists)
credit_ratios = [d / max_credit_d if max_credit_d > 0 else 1.0/N for d in credit_dists]

print("N={} center=({:.0f},{:.0f}) inner_r={:.0f}".format(N, center[0], center[1], inner_r))
print()
print("{:>8s}  {:>6s}  {:>7s}  {:>7s}  {:>6s}".format("Angle", "AxisD", "Score", "CredD", "Cred%"))
print("-" * 50)

for i in range(N):
    angle = slice_angle * i * 2
    score_dist = axis_dists[i]
    score = (score_dist / inner_r) ** 0.25 * 100 if inner_r > 0 else 0
    cred_d = credit_dists[i]
    cred_pct = credit_ratios[i] * 100
    print("{:>8.1f}  {:>6.0f}  {:>7.2f}  {:>7.0f}  {:>6.1f}".format(
        math.degrees(angle), score_dist, score, cred_d, cred_pct))

# Also try: detect credit polygon by color (low-saturation fill)
print()
print("Trying credit detection via lower S mask:")
for s_cred in range(60, 130, 10):
    cred_mask = cv2.inRange(hsv, np.array([80, s_cred, 40]), np.array([160, 255, 255]))
    cred_mask = cv2.dilate(cred_mask, k, 1); cred_mask = cv2.erode(cred_mask, k, 1)
    # How many sectors have this mask?
    hits = 0
    for i in range(N):
        mid_angle = slice_angle * (i * 2 + 1)
        for d in range(10, int(min(w,h)*0.4), 5):
            px = int(center[0] + d * math.cos(mid_angle))
            py = int(center[1] + d * math.sin(mid_angle))
            if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
            if cred_mask[py, px] > 0:
                hits += 1
                break
    print("  S>{}: {}/{} sectors hit".format(s_cred, hits, N))
