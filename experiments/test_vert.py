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

# Find the contour near (610,451) - this is the blue polygon
for i, cnt in enumerate(contours):
    if hierarchy[0][i][3] != -1: continue
    ctr = np.mean(cnt.reshape(-1,2), axis=0)
    if abs(ctr[0]-610)>100 or abs(ctr[1]-451)>100: continue
    area = cv2.contourArea(cnt)
    if area < 5000: continue
    
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.01*peri, True)
    verts = np.array([v[0] for v in approx if 5<v[0][0]<w-5 and 5<v[0][1]<h-5])
    
    # Center = direct centroid of polygon vertices
    center = np.mean(verts, axis=0)
    
    # Angles and distances of vertices
    angles = [math.atan2(v[1]-center[1], v[0]-center[0]) for v in verts]
    dists = [np.linalg.norm(v-center) for v in verts]
    
    # Sort by angle
    order = sorted(range(len(angles)), key=lambda j: angles[j])
    sorted_dists = [dists[j] for j in order]
    sorted_angles = [angles[j] for j in order]
    
    inner_r = max(sorted_dists)
    scores = [(d/inner_r)**0.25*100 for d in sorted_dists]
    
    # reference credits (adjusted +2)
    cred = [4,3,2,4,2,2,2,1,3,1,2,5,3,2,1,1]
    
    N_verts = len(sorted_dists)
    N_cred = len(cred)
    n = min(N_verts, N_cred)
    
    print("Center=({:.0f},{:.0f}) verts={} inner_r={:.0f}".format(center[0], center[1], N_verts, inner_r))
    print("{:>3s} {:>8s} {:>7s} {:>7s} {:>6s}".format("#","Angle","Dist","Score","Cred"))
    print("-"*38)
    for j in range(n):
        ang = math.degrees(sorted_angles[j])
        print("{:>3d} {:>8.1f} {:>7.0f} {:>7.2f} {:>6d}".format(j, ang, sorted_dists[j], scores[j], cred[j]))
    
    w_sum = sum(scores[j]*cred[j] for j in range(n))
    w_avg = w_sum / sum(cred[:n])
    gt_sum = sum([95,76,83,88,91,99,83,79,95,69,100,98,99,94,95,94][j]*cred[j] for j in range(n))
    gt_avg = gt_sum / sum(cred[:n])
    print("\nWeighted avg: {:.2f} (GT from reference scores: {:.2f})".format(w_avg, gt_avg))
    break
