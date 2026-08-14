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

# Refined credit detection: find where color fill ends and gray bg begins
# Credit polygon fill: S >= 10 (moderate saturation), V varies
# Gray background: S < 5, V ~ 180
# White elements: S < 5, V > 240 (ignore these)

print("Testing refined credit detection (S<5 AND V between 150-210):")
print("{:>8s}  {:>8s}  {:>8s}".format("Sector", "CredR", "Credit%"))
print("-" * 35)

credit_dists = []
for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    
    # First confirm we start inside the credit polygon  
    test_r = inner_r * 0.5
    px0 = int(center[0] + test_r * math.cos(mid_angle))
    py0 = int(center[1] + test_r * math.sin(mid_angle))
    if not (0 <= px0 < w and 0 <= py0 < h):
        credit_dists.append(outer_r)
        continue
    
    s_inside = int(S[py0, px0])
    v_inside = int(V[py0, px0])
    
    found_edge = 0
    low_s_count = 0
    
    for d in range(int(inner_r * 0.3), int(outer_r * 3), 2):
        px = int(center[0] + d * math.cos(mid_angle))
        py = int(center[1] + d * math.sin(mid_angle))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: break
        
        s_val = int(S[py, px])
        v_val = int(V[py, px])
        
        # Gray background: S~0, V~180
        # White areas: S~0, V~255
        is_gray_bg = (s_val < 5 and 150 < v_val < 210)
        
        if is_gray_bg:
            low_s_count += 1
            if low_s_count >= 3 and found_edge == 0:
                found_edge = d
        else:
            low_s_count = 0
    
    # If no edge found, credit polygon extends to outer_r
    if found_edge == 0:
        # Try looser condition: just check if we're still in colored area at outer_r
        px_outer = int(center[0] + outer_r * math.cos(mid_angle))
        py_outer = int(center[1] + outer_r * math.sin(mid_angle))
        if 0 <= px_outer < w and 0 <= py_outer < h:
            s_outer = int(S[py_outer, px_outer])
            v_outer = int(V[py_outer, px_outer])
            if s_outer >= 5:
                found_edge = outer_r  # Fill extends to outer ring
            else:
                found_edge = outer_r * 0.5  # Assume half
    
    credit_dists.append(float(found_edge) if found_edge > 0 else float(outer_r))
    
    cred_pct = credit_dists[-1] / outer_r * 100 if outer_r > 0 else 0
    print("{:>8d}  {:>8.0f}  {:>7.1f}%".format(i, credit_dists[-1], min(cred_pct, 100)))

# Normalize and estimate credits
total_credits = 38  # TERM_B total (36) + 2
cred_ratios = [min(d / outer_r, 1.0) for d in credit_dists]
cred_estimates = [r * total_credits / sum(cred_ratios) for r in cred_ratios]

print()
print("Credit estimates (total={}):".format(total_credits))
for i in range(N):
    print("  sector{}: {:.1f} credits".format(i, cred_estimates[i]))
print("  sum: {:.1f}".format(sum(cred_estimates)))
