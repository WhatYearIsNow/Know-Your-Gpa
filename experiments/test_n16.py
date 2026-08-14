import cv2, numpy as np, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Try lower S thresholds to find a polygon with ~16 vertices
for s_min in [120, 125, 130, 135, 140, 145, 150]:
    mask = cv2.inRange(hsv, np.array([85, s_min, 40]), np.array([160, 255, 255]))
    k = np.ones((2,2), np.uint8)
    mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    total = w * h
    for i, cnt in enumerate(contours):
        if hierarchy[0][i][3] != -1: continue
        area = cv2.contourArea(cnt)
        if area < 5000 or area > total * 0.7: continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.015*peri, True)
        nv = len(approx)
        if nv >= 10:
            ctr = np.mean(approx.reshape(-1,2), axis=0)
            # Count how many inner verts (not at boundary)
            verts = approx.reshape(-1,2)
            margin = 5
            inner = [v for v in verts if margin<v[0]<w-margin and margin<v[1]<h-margin]
            print("S>{}: nv={} inner={} center=({:.0f},{:.0f}) area={:.0f}".format(
                s_min, nv, len(inner), ctr[0], ctr[1], area))
