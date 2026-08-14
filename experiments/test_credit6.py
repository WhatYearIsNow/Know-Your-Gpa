import cv2, numpy as np, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
S = hsv[:,:,1]
V = hsv[:,:,2]

center = np.array([297.0, 640.0])
N = 8
slice_angle = math.pi / N
inner_r = 94
outer_r = inner_r * 1.5

# For each sector, scan radially at fine resolution and find the boundary
# where color (saturation) ends and background begins
# White bg has V~255, gray bg has V~181
# The credit polygon has moderate S (varies)

print("Fine-grained credit boundary detection:")
print("{:>8s}  {:>6s}  {:>8s}  {:>7s}".format("Sector", "EdgeR", "SatDrop", "Credit%"))
print("-" * 40)

credit_dists = []
for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    
    # Scan at 1px resolution, track S values
    s_history = []
    for d in range(int(inner_r * 0.2), int(outer_r * 3), 1):
        px = int(center[0] + d * math.cos(mid_angle))
        py = int(center[1] + d * math.sin(mid_angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        s_history.append((d, int(S[py, px]), int(V[py, px])))
    
    # Find first sustained S drop (5+ consecutive low-S pixels)
    # where the subsequent V is NOT white (V<230 - distinguishes from white gaps)
    found_edge = 0
    low_s_start = -1
    for j, (d, s_val, v_val) in enumerate(s_history):
        if s_val < 8 and v_val < 230:  # low S and not white
            if low_s_start < 0:
                low_s_start = d
            if d - low_s_start >= 4:  # 5 consecutive pixels (4 pixel gap)
                found_edge = low_s_start
                break
        else:
            low_s_start = -1
    
    if found_edge == 0:
        # Check if we even HAVE any low-S region - maybe fill extends to outer_r
        # Find the first low-S region (even if white)
        for j, (d, s_val, v_val) in enumerate(s_history):
            if s_val < 8:  # any low-S
                if v_val >= 230:
                    # white gap - keep going
                    continue
                found_edge = d
                break
    
    credit_dists.append(float(found_edge) if found_edge > 0 else float(outer_r))
    
    cred_pct = credit_dists[-1] / outer_r * 100 if outer_r > 0 else 0
    # Find saturation at the edge for reference
    if found_edge > 0:
        px_e = int(center[0] + found_edge * math.cos(mid_angle))
        py_e = int(center[1] + found_edge * math.sin(mid_angle))
        s_at_edge = int(S[py_e, px_e]) if 0<=px_e<w and 0<=py_e<h else -1
    else:
        s_at_edge = -1
    print("{:>8d}  {:>6.0f}  {:>8d}  {:>7.1f}%".format(
        i, credit_dists[-1], s_at_edge, cred_pct))

# Normalize credits
total_credits = 38
cred_ratios = [min(d / outer_r, 1.0) for d in credit_dists]
sum_r = sum(cred_ratios)
cred_estimates = [r * total_credits / sum_r for r in cred_ratios]

print()
print("Estimated credits (total={}):".format(total_credits))
for i in range(N):
    print("  sector{}: {:.1f}".format(i, cred_estimates[i]))
print("  sum: {:.1f}".format(sum(cred_estimates)))
