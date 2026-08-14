import cv2, numpy as np, math

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

mask = cv2.inRange(hsv, np.array([85, 130, 40]), np.array([160, 255, 255]))
k = np.ones((2,2), np.uint8)
mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)
contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

for i, cnt in enumerate(contours):
    if hierarchy[0][i][3] != -1: continue
    ctr = np.mean(cnt.reshape(-1,2), axis=0)
    if abs(ctr[0]-610)>100 or abs(ctr[1]-451)>100: continue
    area = cv2.contourArea(cnt)
    if area < 5000: continue
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.01*peri, True)
    verts = np.array([v[0] for v in approx if 5<v[0][0]<w-5 and 5<v[0][1]<h-5])
    center = np.mean(verts, axis=0)
    angles = [math.atan2(v[1]-center[1], v[0]-center[0]) for v in verts]
    dists = [np.linalg.norm(v-center) for v in verts]
    order = sorted(range(len(angles)), key=lambda j: angles[j])
    sorted_dists = [dists[j] for j in order]
    inner_r = max(sorted_dists)
    scores = [(d/inner_r)**0.25*100 for d in sorted_dists]
    cred = [4,3,2,4,2,2,2,1,3,1,2,5,3,2,1,1]
    n = min(len(scores), len(cred))
    print("Weighted avg: {:.2f}".format(sum(scores[j]*cred[j] for j in range(n))/sum(cred[:n])))
    break
