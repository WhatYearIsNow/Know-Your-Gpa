import cv2, numpy as np, math

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Blue polygon mask
mask = cv2.inRange(hsv, np.array([85, 130, 40]), np.array([160, 255, 255]))
k = np.ones((2,2), np.uint8)
mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)

# Center = centroid of all blue pixels
ys, xs = np.where(mask > 0)
center = np.array([np.mean(xs), np.mean(ys)])
print("Center via pixel centroid: ({:.0f},{:.0f})".format(center[0], center[1]))

# N=16 radial scan
N = 16; sl = math.pi / N
dists = []
for i in range(N):
    angle = sl * i * 2
    fd = 0
    for d in range(1, int(min(w,h)), 1):
        px = int(center[0] + d * math.cos(angle))
        py = int(center[1] + d * math.sin(angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        if mask[py, px] > 0:
            fd = d
        elif fd > 0:
            break
    dists.append(float(fd))

inner_r = max(dists)
scores = [(d/inner_r)**0.25*100 if inner_r>0 else 0 for d in dists]

# Also refine: recompute center as mean of inner 50% distances
# (exclude boundary outliers)

cred = [4,3,2,4,2,2,2,1,3,1,2,5,3,2,1,1]

print("inner_r={:.0f}".format(inner_r))
print("{:>4s} {:>6s} {:>7s} {:>7s}".format("Axis", "Angle", "Dist", "Score"))
print("-" * 30)
for i in range(N):
    print("{:>4d} {:>6.0f} {:>7.0f} {:>7.2f}".format(i, math.degrees(sl*i*2), dists[i], scores[i]))

w_avg = sum(scores[i]*cred[i] for i in range(N)) / sum(cred)
print("\nWeighted avg: {:.2f}".format(w_avg))
