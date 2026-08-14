import cv2, numpy as np, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures", "occluded-sample.jpg")
with open(path, "rb") as fp: raw = fp.read()
img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
S = hsv[:,:,1]; V = hsv[:,:,2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

center = np.array([297.0, 640.0])
N = 8; sl = math.pi / N
inner_r = 94; outer_r = inner_r * 1.5

# For each sector midpoint, do a fine radial scan and report S and gray values
print("Radial S+gray scan per sector:")
for i in range(N):
    ma = sl * (i * 2 + 1)
    print("\nsector{} at {:.1f} deg:".format(i, math.degrees(ma)))
    for r in range(int(inner_r*0.3), int(outer_r*2.5), 20):
        px = int(center[0] + r * math.cos(ma))
        py = int(center[1] + r * math.sin(ma))
        if px < 2 or px >= w-2 or py < 2 or py >= h-2: continue
        s_val = int(S[py, px])
        v_val = int(V[py, px])
        g_val = int(gray[py, px])
        # Mark: inside credit fill? outside?
        tag = ""
        if s_val < 5: tag = " GRAY_BG"
        elif s_val > 150: tag = " BLUE_POLY"
        print("  r={:>4d}: S={:>3d} V={:>3d} gray={:>3d}{}".format(r, s_val, v_val, g_val, tag))
