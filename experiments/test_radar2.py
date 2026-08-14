import cv2, numpy as np, math, os

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures")

def parse_gt(txt_path):
    courses = []
    with open(txt_path, "r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line: continue
            parts = line.split("\t")
            if len(parts) < 8: continue
            try: credit = float(parts[5])
            except ValueError: continue
            if credit <= 0: continue
            try: score = float(parts[-2].strip())
            except ValueError: continue
            if score <= 0: continue
            try: gpa = float(parts[-1].strip())
            except ValueError: gpa = 0.0
            courses.append({"name": parts[2], "credit": credit, "score": score, "gpa": gpa})
    return courses

for f in sorted(os.listdir(IMG_DIR)):
    if not f.endswith(".jpg"): continue
    base = f[:-4]; txt = base + ".txt"
    img_path = os.path.join(IMG_DIR, f)
    gt_path = os.path.join(IMG_DIR, txt)
    if not os.path.exists(gt_path): continue
    gt = parse_gt(gt_path)
    with open(img_path, "rb") as fp: raw = fp.read()
    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s_min = 155 if "reference2" in f else 150
    mask = cv2.inRange(hsv, np.array([90, s_min, 50]), np.array([150, 255, 255]))
    k = np.ones((2,2), np.uint8); mask = cv2.dilate(mask, k, 1); mask = cv2.erode(mask, k, 1)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    total = w * h; best_i = None; best_area = 0
    for i, cnt in enumerate(contours):
        if hierarchy[0][i][3] != -1: continue
        area = cv2.contourArea(cnt)
        if area > total * 0.95: continue
        if area > best_area: best_area = area; best_i = i
    if best_i is None: continue
    cnt = contours[best_i]
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.015*peri, True)
    all_verts = approx.reshape(-1, 2).astype(np.float64)
    margin = 3
    inner_verts = np.array([v for v in all_verts
        if margin < v[0] < w - margin and margin < v[1] < h - margin])
    if len(inner_verts) < 3:
        print("{} inner verts={} too few".format(f, len(inner_verts)))
        continue
    center = np.mean(inner_verts, axis=0)
    dists = [np.linalg.norm(v - center) for v in inner_verts]
    angles = [math.atan2(v[1]-center[1], v[0]-center[0]) for v in inner_verts]
    sorted_idx = sorted(range(len(angles)), key=lambda i: angles[i])
    sorted_dists = [dists[i] for i in sorted_idx]
    sorted_angles = [angles[i] for i in sorted_idx]
    inner_r = max(sorted_dists)
    scores = [(d / inner_r) ** 0.25 * 100 for d in sorted_dists]
    n = min(len(scores), len(gt))
    print()
    print("=== " + f + " ===")
    print("  Inner verts={} GT={} matched={}".format(len(inner_verts), len(gt), n))
    print("  center=({:.0f},{:.0f}) inner_r={:.0f}".format(center[0], center[1], inner_r))
    hdr = "  {:>8s}  {:>6s}  {:>7s}  {:>7s}  {:>7s}  {}".format("Angle", "Dist", "Det", "GT", "Err", "Course")
    print(hdr)
    print("  " + "-" * 58)
    errs = []
    total_cr = sum(c["credit"] for c in gt)
    w_gt = sum(c["score"]*c["credit"] for c in gt)/total_cr
    w_det_sum = 0
    for i in range(n):
        ds = scores[i]; gs = gt[i]["score"]; err = ds - gs
        errs.append(err)
        nm = gt[i]["name"][:20]
        print("  {:>8.1f}  {:>6.0f}  {:>7.2f}  {:>7.2f}  {:>+7.2f}  {}".format(
            math.degrees(sorted_angles[i]), sorted_dists[i], ds, gs, err, nm))
        w_det_sum += ds * gt[i]["credit"]
    if errs:
        mae = sum(abs(e) for e in errs)/len(errs)
        rmse = math.sqrt(sum(e**2 for e in errs)/len(errs))
        w_det = w_det_sum / total_cr
        print("  " + "-" * 58)
        print("  MAE={:.2f}  RMSE={:.2f}".format(mae, rmse))
        print("  Weighted: det={:.2f} gt={:.2f} err={:+.2f}".format(w_det, w_gt, w_det-w_gt))
