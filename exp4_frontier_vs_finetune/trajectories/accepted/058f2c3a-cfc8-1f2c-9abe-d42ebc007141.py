# 058f2c3a-cfc8-1f2c-9abe-d42ebc007141 — agentic final (cand 1), IoU 0.824
from build123d import *

# ---- dimensions read from the drawing ----
L       = 84.0   # mm  overall length (X), FRONT/TOP views
W       = 50.0   # mm  overall width  (Y), RIGHT view
T       = 7.0    # mm  plate thickness (Z), FRONT view
hole_d  = 3.0    # mm  "8x Ø3 THRU (2x4)"
x_edge  = 10.0   # mm  -X edge to first hole column (TOP)
x_pitch = 22.7   # mm  column pitch, "3x 22.7" (TOP)
y_pitch = 38.0   # mm  row spacing, "1x 38" (TOP); row margin (W-38)/2 = 6 = RIGHT-view "6"

# ---- derived positions (from the -X / -Y edges), then centered on origin ----
x_cols = [x_edge + i * x_pitch for i in range(4)]          # 10, 32.7, 55.4, 78.1
y_rows = [(W - y_pitch) / 2, (W - y_pitch) / 2 + y_pitch]  # 6, 44
xc = [x - L / 2 for x in x_cols]                           # -32, -9.3, 13.4, 36.1
yc = [y - W / 2 for y in y_rows]                           # -19, +19
hole_pts = [(x, y) for y in yc for x in xc]

with BuildPart() as bp:
    Box(L, W, T)  # centered: X +/-42, Y +/-25, Z +/-3.5
    with Locations(hole_pts):
        Cylinder(radius=hole_d / 2, height=T, mode=Mode.SUBTRACT)  # through the 7 mm plate

part = bp.part
export_step(part, "output.step")
