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
    print()
    print("=== " + f + " ===")
    gt = parse_gt(gt_path)
    print("  GT: " + str(len(gt)) + " courses")
    total_cr = sum(c["credit"] for c in gt)
    w_gt = sum(c["score"]*c["credit"] for c in gt)/total_cr
    print("  Expected weighted: {:.2f}".format(w_gt))
    with open(img_path, "rb") as fp:
        raw = fp.read()
    img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None: continue
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s_min = 155 if "reference2" in f else 150
    low = np.array([90, s_min, 50])
    high = np.array([150, 255, 255])
    mask = cv2.inRange(hsv, low, high)
    k = np.ones((2,2), np.uint8)
    mask = cv2.dilate(mask, k, 1)
    mask = cv2.erode(mask, k, 1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours: print("  No contours!"); continue
    main = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(main, True)
    approx = cv2.approxPolyDP(main, 0.015*peri, True)
    verts = approx.reshape(-1, 2).astype(np.float64)
    center = np.mean(verts, axis=0)
    dists = [np.linalg.norm(v - center) for v in verts]
    angles = [math.atan2(v[1]-center[1], v[0]-center[0]) for v in verts]
    inner_r = max(dists)
    scores = [(d / inner_r) ** 0.25 * 100 for d in dists]
    gt_sorted = sorted(gt, key=lambda c: c["score"])
    det_sorted = sorted(zip(scores, dists, angles), key=lambda x: x[0])
    n = min(len(det_sorted), len(gt_sorted))
    print("  Verts={} matched={}/{} center=({:.0f},{:.0f}) inner_r={:.0f}".format(len(verts), n, len(gt), center[0], center[1], inner_r))
    print("  {:>7s}  {:>7s}  {:>7s}  {}".format("Det", "GT", "Err", "Course"))
    print("  " + "-" * 48)
    errs = []
    for i in range(n):
        ds = det_sorted[i][0]; gs = gt_sorted[i]["score"]
        err = ds - gs; errs.append(err)
        nm = gt_sorted[i]["name"][:18]
        print("  {:>7.2f}  {:>7.2f}  {:>+7.2f}  {}".format(ds, gs, err, nm))
    if errs:
        mae = sum(abs(e) for e in errs)/len(errs)
        rmse = math.sqrt(sum(e**2 for e in errs)/len(errs))
        print("  " + "-" * 48)
        print("  MAE={:.2f}  RMSE={:.2f}".format(mae, rmse))
        w_det = sum(det_sorted[i][0]*gt_sorted[i]["credit"] for i in range(n))/total_cr
        print("  Weighted: det={:.2f} gt={:.2f} err={:+.2f}".format(w_det, w_gt, w_det-w_gt))
