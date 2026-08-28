# 000bc5ac-ffb4-009a-e213-ec6618d29e54 — agentic final (cand 1), IoU 0.965
from build123d import *

# ---- dimensions read from the drawing (mm) ----
L = 60.0        # mm  overall length (X), top/front views
W = 40.0        # mm  overall width  (Y), right view
H = 8.0         # mm  overall height (Z), front/right views
t_floor = 2.0   # mm  bottom floor thickness (front/right "2")
t_wall = 2.0    # mm  perimeter rim (wall) thickness (front "2", top inset)
gate_w = 20.0   # mm  side notch width along Y (right view "20")
d_hole = 5.0    # mm  through-hole diameter ("2x dia5 THRU")
x_h1 = 15.0     # mm  first hole centre from -X edge
x_h2 = 45.0     # mm  second hole centre from -X edge
y_h = W / 2     # mm  holes centred across the width (=20, by symmetry)

# ---- derived values ----
cav_l = L - 2 * t_wall        # 56 mm inner cavity length (X)
cav_w = W - 2 * t_wall        # 36 mm inner cavity width  (Y)
cav_h = H - t_floor           # 6  mm cavity depth (Z=2..8)
gate_y0 = (W - gate_w) / 2    # 10 mm gate start in Y (centred)

with BuildPart() as _bp:
    # outer block 60 x 40 x 8 (corner at origin)
    Box(L, W, H, align=(Align.MIN, Align.MIN, Align.MIN))

    # hollow the top: leaves a 2 mm floor and 2 mm perimeter walls
    with Locations((t_wall, t_wall, t_floor)):
        Box(cav_l, cav_w, cav_h,
            align=(Align.MIN, Align.MIN, Align.MIN),
            mode=Mode.SUBTRACT)

    # gate (notch) through the +X wall only, down to the floor
    with Locations((L - t_wall, gate_y0, t_floor)):
        Box(t_wall, gate_w, cav_h,
            align=(Align.MIN, Align.MIN, Align.MIN),
            mode=Mode.SUBTRACT)

    # two through holes in the floor
    with Locations((x_h1, y_h, 0.0), (x_h2, y_h, 0.0)):
        Cylinder(radius=d_hole / 2, height=H,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = _bp.part
export_step(part, "output.step")
