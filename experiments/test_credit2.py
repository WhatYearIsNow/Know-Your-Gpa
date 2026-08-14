import cv2, numpy as np, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Known params from detection
center = np.array([297.0, 640.0])
N = 8
slice_angle = math.pi / N
inner_r = 94

# Sample color in credit polygon region
# Credit polygon should be at mid-angles between axes, at various radii
print("Sampling credit polygon regions:")
for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    # Sample at multiple radii
    for r_frac in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        r = inner_r * r_frac
        px = int(center[0] + r * math.cos(mid_angle))
        py = int(center[1] + r * math.sin(mid_angle))
        if px < 0 or px >= w or py < 0 or py >= h: continue
        bgr = img[py, px]
        hsv_val = hsv[py, px]
        print("  sector{} r={:.0f} BGR=({},{},{}) HSV=({},{},{}) gray={}".format(
            i, r, bgr[0], bgr[1], bgr[2], hsv_val[0], hsv_val[1], hsv_val[2], gray[py,px]))

# Also try: detect outer ring by looking for the circle of radial line endpoints
# Use radial scan along each axis direction, looking for the line endpoint (sharp edge)
print()
print("Radial scan along axes for inner ring detection:")
for i in range(N):
    angle = slice_angle * i * 2
    prev_val = gray[int(center[1]), int(center[0])]
    edges_found = []
    for d in range(5, int(inner_r * 3), 1):
        px = int(center[0] + d * math.cos(angle))
        py = int(center[1] + d * math.sin(angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        curr_val = gray[py, px]
        if abs(curr_val - prev_val) > 15:
            edges_found.append((d, curr_val - prev_val))
        prev_val = curr_val
    if edges_found:
        print("  axis{}: edges at {}".format(i, [(d, "{:+d}".format(int(diff))) for d, diff in edges_found[:5]]))
