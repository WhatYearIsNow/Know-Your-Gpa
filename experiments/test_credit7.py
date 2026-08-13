import cv2, numpy as np, math, os

path = r"D:\project\Know-Your-Gpa\测试集\occluded-sample.jpg"
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

# Credit polygon fill: moderate saturation (5 < S < 140)
# Blue score polygon: high saturation (S > 145)
# Background: near-zero saturation (S < 5)
cred_mask = cv2.inRange(hsv, np.array([80, 5, 30]), np.array([160, 140, 255]))

# For each sector, find the max radius where credit fill exists
print("Credit polygon via moderate-S mask (5<S<140):")
print("{:>8s}  {:>8s}  {:>8s}".format("Sector", "MaxR", "Credit%"))
print("-" * 35)

credit_dists = []
for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    max_r = 0
    # Scan outward at the sector midpoint
    for d in range(5, int(outer_r * 3), 1):
        px = int(center[0] + d * math.cos(mid_angle))
        py = int(center[1] + d * math.sin(mid_angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        if cred_mask[py, px] > 0:
            max_r = d
    
    credit_dists.append(float(max_r) if max_r > 0 else outer_r * 0.3)
    
    cred_pct = credit_dists[-1] / outer_r * 100 if outer_r > 0 else 0
    print("{:>8d}  {:>8.0f}  {:>7.1f}%".format(i, credit_dists[-1], min(cred_pct, 100)))

# Also check: maybe we should detect outer ring differently
# The credit polygon has outer points at distance outer from center
# These are at angles slice * (i*2 + 1) - halfway between axes
# The credit polygon boundary should have a DROP in saturation
print()
print("Also: check for credit polygon at outerPoints angles (halfway between axes)")
print("Credit polygon vertices should be at:")
for i in range(N):
    outer_angle = slice_angle * (i * 2 + 1)  # This IS the sector midpoint!
    px_o = int(center[0] + outer_r * math.cos(outer_angle))
    py_o = int(center[1] + outer_r * math.sin(outer_angle))
    if 0 <= px_o < w and 0 <= py_o < h:
        s_o = int(S[py_o, px_o])
        v_o = int(V[py_o, px_o])
        print("  outerPt[{}] at ({},{}) S={} V={}".format(i, px_o, py_o, s_o, v_o))

# Ratio-based credit estimation
print()
print("Credit ratios from fill extent:")
cred_ratios = [min(d / outer_r, 1.0) for d in credit_dists]
total_credits = 38
sum_r = sum(cred_ratios)
for i in range(N):
    est = cred_ratios[i] * total_credits / sum_r
    print("  sector{}: {:.1f} credits ({:.0f}% of outer)".format(i, est, cred_ratios[i]*100))
print("  sum: {:.1f}".format(sum(cred_ratios) * total_credits / sum_r))
