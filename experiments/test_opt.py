import cv2, numpy as np, math

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

mask = cv2.inRange(hsv, np.array([85, 130, 40]), np.array([160, 255, 255]))
k = np.ones((2,2), np.uint8)
mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)

# Get polygon contour  
contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
best = None; best_v = 0
for i, cnt in enumerate(contours):
    if hierarchy[0][i][3] != -1: continue
    area = cv2.contourArea(cnt)
    if area < 5000 or area > w*h*0.5: continue
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.005*peri, True)
    inner = np.array([v[0] for v in approx if 5<v[0][0]<w-5 and 5<v[0][1]<h-5])
    if len(inner) >= 12 and len(inner) > best_v:
        best_v = len(inner); best = cnt

peri = cv2.arcLength(best, True)
approx = cv2.approxPolyDP(best, 0.005*peri, True)
verts = np.array([v[0] for v in approx if 5<v[0][0]<w-5 and 5<v[0][1]<h-5])

# Grid search for best center that maximizes total hit distance
best_center = np.mean(verts, axis=0)
best_score = 0
N = 16; sl = math.pi / N

for dx in range(-40, 41, 5):
    for dy in range(-40, 41, 5):
        cx = best_center[0] + dx
        cy = best_center[1] + dy
        total_d = 0
        for i in range(N):
            angle = sl * i * 2
            for d in range(5, int(min(w,h)), 1):
                px = int(cx + d * math.cos(angle))
                py = int(cy + d * math.sin(angle))
                if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
                if mask[py, px] > 0:
                    total_d += d
                    break
        if total_d > best_score:
            best_score = total_d
            best_center = np.array([cx, cy])

print("Optimized center: ({:.0f},{:.0f})".format(best_center[0], best_center[1]))

# Final radial scan from best center
dists = []
for i in range(N):
    angle = sl * i * 2
    fd = 0
    for d in range(1, int(min(w,h)), 1):
        px = int(best_center[0] + d * math.cos(angle))
        py = int(best_center[1] + d * math.sin(angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        if mask[py, px] > 0:
            fd = d
        elif fd > 0:
            break
    dists.append(float(fd))

inner_r = max(dists)
scores = [(d/inner_r)**0.25*100 if inner_r>0 else 0 for d in dists]
cred = [4,3,2,4,2,2,2,1,3,1,2,5,3,2,1,1]

print("inner_r={:.0f}".format(inner_r))
print("{:>4s} {:>6s} {:>7s} {:>7s}".format("Axis","Angle","Dist","Score"))
print("-"*30)
for i in range(N):
    print("{:>4d} {:>6.0f} {:>7.0f} {:>7.2f}".format(i, math.degrees(sl*i*2), dists[i], scores[i]))

w_avg = sum(scores[i]*cred[i] for i in range(N)) / sum(cred)
print("\nWeighted avg: {:.2f}".format(w_avg))
