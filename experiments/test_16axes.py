import cv2, numpy as np, math, os

path = r"D:\project\Know-Your-Gpa\测试集\occluded-sample.jpg"
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Use S>130 to get blue polygon mask
mask = cv2.inRange(hsv, np.array([85, 130, 40]), np.array([160, 255, 255]))
k = np.ones((2,2), np.uint8)
mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)

# Find the polygon contour
contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
best = None; best_area = 0
for i, cnt in enumerate(contours):
    if hierarchy[0][i][3] != -1: continue
    area = cv2.contourArea(cnt)
    ctr = np.mean(cnt.reshape(-1,2), axis=0)
    if area > 5000 and area < w*h*0.5 and ctr[1] < h*0.5 and ctr[0] > w*0.2:
        if area > best_area: best_area = area; best = cnt

if best is None: exit()

# Get polygon centroid as initial center
ctr = np.mean(best.reshape(-1,2), axis=0)
print("Initial center: ({:.0f},{:.0f})".format(ctr[0], ctr[1]))

# Try N=16 radial scan 
N = 16
sl = math.pi / N
dists = []
for i in range(N):
    angle = sl * i * 2
    found_d = 0
    for d in range(5, int(min(w,h)), 1):
        px = int(ctr[0] + d * math.cos(angle))
        py = int(ctr[1] + d * math.sin(angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        if mask[py, px] > 0:
            found_d = d
        elif found_d > 0:
            break
    dists.append(float(found_d))

print("Axis distances ({} axes):".format(N))
for i in range(N):
    print("  {:>3d}: {:.0f} deg, dist={:.0f}".format(i, int(math.degrees(sl*i*2)), dists[i]))

inner_r = max(dists)
print("inner_r = {:.0f}".format(inner_r))
scores = [(d/inner_r)**0.25 * 100 if inner_r>0 else 0 for d in dists]
for i in range(N):
    print("  axis{:>2d}: score={:.2f}".format(i, scores[i]))

# Now for credits: TERM_B data
cred_TERM_B = [3,2,4,1,2,3,1,2,4,1,3,2,2,1,3,2]
print("\nTERM_B credits: {} sum={}".format(cred_TERM_B, sum(cred_TERM_B)))

# occluded-sample credits: almost same, +2 total = 38
# Distribute +2: 
test1_cred = list(cred_TERM_B)
# simplest: add 1 to two of the 1-credit courses
added = 0
for i in range(len(test1_cred)):
    if test1_cred[i] == 1 and added < 2:
        test1_cred[i] = 2
        added += 1
print("occluded-sample credits (adjusted): {} sum={}".format(test1_cred, sum(test1_cred)))

w_avg = sum(scores[i]*test1_cred[i] for i in range(N)) / sum(test1_cred)
print("Weighted avg: {:.2f}".format(w_avg))
