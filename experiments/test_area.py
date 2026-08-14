import cv2, numpy as np, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

center = np.array([297.0, 640.0])
N = 8
slice_angle = math.pi / N
inner_r = 94

# Create a mask specifically for the CREDIT polygon fill
# Sampled credit fill: H~107, S~130, V~227
# Background gray: H~0, S~0, V~181
# Blue polygon: H~105, S~150, V~211
x0 = int(center[0] + inner_r*0.8 * math.cos(slice_angle * 1))
y0 = int(center[1] + inner_r*0.8 * math.sin(slice_angle * 1))
ref_hsv = hsv[y0, x0]
print("Reference credit fill HSV: H={} S={} V={}".format(ref_hsv[0], ref_hsv[1], ref_hsv[2]))

# Tight mask for credit fill
cred_mask = cv2.inRange(hsv, 
    np.array([100, 100, 210]), 
    np.array([115, 150, 240]))
    
print("Credit mask total pixels: {}".format(cv2.countNonZero(cred_mask)))

# For each sector, count credit fill pixels at different radii
print()
print("Credit fill per sector (pixel count in radial bins):")
print("{:>6s}".format("Sector"), end="")
for r_bin in range(1, 7):
    print("  r{:d}".format(r_bin), end="")
print()

for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    print("  {:>4d}".format(i), end="")
    for r_bin in range(1, 7):
        # Count credit fill pixels in this sector at this radial bin
        # Bin bounds: (r_bin-1)*inner_r/3 to r_bin*inner_r/3
        r_start = (r_bin - 1) * inner_r / 3
        r_end = r_bin * inner_r / 3
        count = 0
        for r in range(int(r_start), int(r_end), 2):
            px = int(center[0] + r * math.cos(mid_angle))
            py = int(center[1] + r * math.sin(mid_angle))
            if 0 <= px < w and 0 <= py < h:
                if cred_mask[py, px] > 0:
                    count += 1
        print("  {:>3d}".format(count), end="")
    print()

# Also compute total credit fill area per sector
print()
print("Total credit fill area per sector:")
for i in range(N):
    mid_angle = slice_angle * (i * 2 + 1)
    total = 0
    for r in range(5, int(inner_r * 3), 2):
        px = int(center[0] + r * math.cos(mid_angle))
        py = int(center[1] + r * math.sin(mid_angle))
        if 0 <= px < w and 0 <= py < h:
            if cred_mask[py, px] > 0:
                total += 1
    print("  sector{}: {} pixels".format(i, total))
