import cv2, numpy as np, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
S = hsv[:,:,1]; V = hsv[:,:,2]
B, G, R = img[:,:,0].astype(float), img[:,:,1].astype(float), img[:,:,2].astype(float)

center = np.array([297.0, 640.0])
N = 8
slice_angle = math.pi / N
inner_r = 94

# Instead of assuming outer_r, detect credit polygon boundary per sector
# by looking for COLOR CHANGE from a reference inside the fill
print("Credit polygon boundary via color-distance scan:")
print("{:>6s}  {:>6s}  {:>7s}".format("Sector", "BoundR", "Credit%"))
print("-" * 30)

credit_bounds = []
for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    
    # Reference: pixel at 40% of inner_r (definitely inside fill)
    ref_r = inner_r * 0.4
    ref_px = int(center[0] + ref_r * math.cos(mid_angle))
    ref_py = int(center[1] + ref_r * math.sin(mid_angle))
    ref_bgr = img[ref_py, ref_px].astype(float)
    
    # Scan outward, compute color distance from reference
    found_edge = 0
    color_dists = []
    for d in range(int(inner_r * 0.2), int(inner_r * 4), 2):
        px = int(center[0] + d * math.cos(mid_angle))
        py = int(center[1] + d * math.sin(mid_angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        curr_bgr = img[py, px].astype(float)
        dist = np.sqrt(np.sum((curr_bgr - ref_bgr) ** 2))
        color_dists.append((d, dist))
    
    # Find the first sustained jump in color distance
    # The credit polygon boundary should have a significant color change
    for j in range(10, len(color_dists) - 3):
        d1, dist1 = color_dists[j]
        _, dist2 = color_dists[j+2]  # look ahead 2 steps
        if dist2 - dist1 > 30:  # significant jump
            found_edge = d1
            break
    
    credit_bounds.append(float(found_edge) if found_edge > 0 else 0.0)
    
    # Normalize relative to max bound
    max_bound = max(credit_bounds) if credit_bounds else 1
    pct = credit_bounds[-1] / max_bound * 100 if max_bound > 0 else 0
    print("{:>6d}  {:>6.0f}  {:>7.1f}%".format(i, credit_bounds[-1], pct))

# Also: check TERM_B data to see credit distribution
print()
print("TERM_B credits: [4, 3, 1, 4, 2, 2, 1, 1, 3, 1, 2, 5, 3, 2, 1, 1]")
cred_vals = [3,2,4,1,2,3,1,2,4,1,3,2,2,1,3,2]
print("Distribution: max={} count of each:".format(max(cred_vals)))
for v in sorted(set(cred_vals), reverse=True):
    print("  {}: {} courses".format(v, cred_vals.count(v)))
print("  total: {}".format(sum(cred_vals)))
