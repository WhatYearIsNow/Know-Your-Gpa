import cv2, numpy as np, math, os

path = r"D:\project\Know-Your-Gpa\测试集\occluded-sample.jpg"
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Use S>145 with wide H range to find the polygon for this image
s_min = 145
mask = cv2.inRange(hsv, np.array([85, s_min, 40]), np.array([160, 255, 255]))
k = np.ones((2,2), np.uint8)
mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)
contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

# Find the contour closest to expected radar chart position (y around 0.35*h)
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
    if d < best_dist:
        best_dist = d
        best = (cnt, approx, nv, ctr)

if best:
    cnt, approx, nv, center = best
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.01*peri, True)  # tighter epsilon
    verts = approx.reshape(-1, 2).astype(np.float64)
    # filter boundary verts
    margin = 5
    inner_verts = np.array([v for v in verts
        if margin < v[0] < w-margin and margin < v[1] < h-margin])
    center = np.mean(inner_verts, axis=0)
    
    N = len(inner_verts)
    print("N={} center=({:.0f},{:.0f}) inner_verts={}".format(N, center[0], center[1], N))
    
    # Radial scan at evenly-spaced axes
    slice_angle = math.pi / N
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
        axis_dists.append(float(found_d) if found_d > 0 else 0.0)
    
    inner_r = max(axis_dists)
    scores = [(d / inner_r) ** 0.25 * 100 if inner_r > 0 else 0 for d in axis_dists]
    
    print("inner_r={:.0f}".format(inner_r))
    print("{:>8s}  {:>6s}  {:>7s}".format("Angle", "Dist", "Score"))
    print("-" * 30)
    for i in range(N):
        angle_deg = math.degrees(slice_angle * i * 2)
        print("{:>8.1f}  {:>6.0f}  {:>7.2f}".format(angle_deg, axis_dists[i], scores[i]))
    
    # Save annotated image
    ann = img.copy()
    for i in range(N):
        angle = slice_angle * i * 2
        ex = int(center[0] + inner_r * 1.3 * math.cos(angle))
        ey = int(center[1] + inner_r * 1.3 * math.sin(angle))
        cv2.line(ann, tuple(center.astype(int)), (ex, ey), (0, 255, 255), 1)
        # data point
        dp = int(center[0] + axis_dists[i] * math.cos(angle))
        dpy = int(center[1] + axis_dists[i] * math.sin(angle))
        cv2.circle(ann, (dp, dpy), 4, (255, 0, 0), -1)
    cv2.circle(ann, tuple(center.astype(int)), 5, (0, 0, 255), -1)
    out = path.replace(".jpg", "_detected.jpg")
    cv2.imwrite(out, ann)
    print("Saved: " + out)
