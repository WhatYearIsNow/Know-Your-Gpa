import cv2, numpy as np, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Try S>130, contour at (610,451) - had 14 verts
# Try much smaller epsilon to get all 16 vertices
s_min = 130
mask = cv2.inRange(hsv, np.array([85, s_min, 40]), np.array([160, 255, 255]))
k = np.ones((2,2), np.uint8)
mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)
contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

# Target the contour near (610, 451)
for i, cnt in enumerate(contours):
    if hierarchy[0][i][3] != -1: continue
    area = cv2.contourArea(cnt)
    peri = cv2.arcLength(cnt, True)
    ctr_raw = np.mean(cnt.reshape(-1,2), axis=0)
    if abs(ctr_raw[0] - 610) < 100 and abs(ctr_raw[1] - 451) < 100 and area > 5000:
        print("Contour at ({:.0f},{:.0f}) area={:.0f} peri={:.0f}".format(ctr_raw[0], ctr_raw[1], area, peri))
        for eps_factor in [0.015, 0.01, 0.008, 0.005, 0.003, 0.002, 0.001]:
            approx = cv2.approxPolyDP(cnt, eps_factor * peri, True)
            verts = approx.reshape(-1,2)
            margin = 5
            inner = [v for v in verts if margin<v[0]<w-margin and margin<v[1]<h-margin]
            print("  eps={:.3f}: nv={} inner={}".format(eps_factor, len(verts), len(inner)))
            if len(inner) >= 15:
                print("    Inner coords: {}".format([(int(v[0]),int(v[1])) for v in inner]))
