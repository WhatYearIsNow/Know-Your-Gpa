import cv2, numpy as np, math

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

mask = cv2.inRange(hsv, np.array([85, 130, 40]), np.array([160, 255, 255]))
k = np.ones((2,2), np.uint8)
mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)

# Get polygon contour and improve center by selecting good contour
contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

# Pick contour near (610,451) - the one with 14 verts originally
for i, cnt in enumerate(contours):
    if hierarchy[0][i][3] != -1: continue
    area = cv2.contourArea(cnt)
    peri = cv2.arcLength(cnt, True)
    ctr = np.mean(cnt.reshape(-1,2), axis=0)
    if abs(ctr[0]-610) > 100 or abs(ctr[1]-451) > 100: continue
    if area < 5000: continue
    
    # Use eps=0.005 to get all 16 verts
    approx = cv2.approxPolyDP(cnt, 0.005*peri, True)
    verts = approx.reshape(-1,2)
    margin = 5
    inner = np.array([v for v in verts if margin<v[0]<w-margin and margin<v[1]<h-margin])
    
    if len(inner) < 12: continue
    
    center = np.mean(inner, axis=0)
    
    # Do radial scan from this center
    N = len(inner)  # use detected N
    N = min(N, 20)
    sl = math.pi / N
    dists = []
    for j in range(N):
        angle = sl * j * 2
        fd = 0
        for d in range(5, int(min(w,h)), 1):
            px = int(center[0] + d * math.cos(angle))
            py = int(center[1] + d * math.sin(angle))
            if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
            if mask[py, px] > 0:
                fd = d
            elif fd > 0:
                break
        dists.append(float(fd))
    
    inner_r = max(dists)
    
    print("Center=({:.0f},{:.0f}) N={} inner_r={:.0f}".format(center[0], center[1], N, inner_r))
    print("Dists:", [round(d) for d in dists])
    
    scores = [(d/inner_r)**0.25*100 if inner_r>0 else 0 for d in dists]
    print("Scores:", [round(s,1) for s in scores])
    
    # Credits from TERM_B (adjusted)
    cred = [4,3,2,4,2,2,2,1,3,1,2,5,3,2,1,1]
    n = min(N, len(cred))
    w_sum = sum(scores[i]*cred[i] for i in range(n))
    c_sum = sum(cred[:n])
    w_avg = w_sum / c_sum
    print("Weighted avg (n={}): {:.2f}".format(n, w_avg))
    break
