# 00199e66-2f80-ae33-2603-60a317088932 — agentic final (cand 1), IoU 1.000
from build123d import *
from math import tan, radians

# ---------- dimensions read from the drawing ----------
plate_L   = 80   # mm  overall length (X)                - top view overall dim
plate_W   = 60   # mm  overall width  (Y)                - right side view overall dim
plate_T   = 12   # mm  plate thickness (Z)               - front view
col_left  = 15   # mm  left hole column from left edge   - top view baseline dim
col_right = 65   # mm  right hole column from left edge  - top view baseline dim
row_front = 15   # mm  front hole row from front edge    - right side view baseline dim
row_back  = 45   # mm  back hole row from front edge     - right side view baseline dim
hole_d    = 5    # mm  through-hole diameter, "4x ⌀5 THRU"
csk_d     = 10   # mm  countersink diameter,  "⌀10 × 82°"
csk_a     = 82   # deg countersink included angle
pocket_d  = 30   # mm  central blind pocket,  "⌀30 ↓6"
pocket_z  = 6    # mm  pocket depth from top face
c1        = 1    # mm  45° chamfer on the 4 corner edges, "C1"

# ---------- derived values ----------
hx    = (col_right - col_left) / 2                        # 25 mm - hole column offset from centre
hy    = (row_back - row_front) / 2                        # 15 mm - hole row offset from centre
csk_h = (csk_d - hole_d) / 2 / tan(radians(csk_a / 2))    # ~2.88 mm - countersink cone height

with BuildPart() as bp:
    # base plate: bottom face on Z=0, centred in X/Y
    Box(plate_L, plate_W, plate_T,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # central blind pocket ⌀30, 6 deep from the top face
    with Locations((0, 0, plate_T - pocket_z)):
        Cylinder(pocket_d / 2, pocket_z + 1,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    # 4x ⌀5 through holes with ⌀10 x 82° countersinks from the top
    with Locations([(sx * hx, sy * hy, plate_T)
                    for sx in (-1, 1) for sy in (-1, 1)]):
        Cylinder(hole_d / 2, plate_T + 2,
                 align=(Align.CENTER, Align.CENTER, Align.MAX),
                 mode=Mode.SUBTRACT)
        Cone(hole_d / 2, csk_d / 2, csk_h,
             align=(Align.CENTER, Align.CENTER, Align.MAX),
             mode=Mode.SUBTRACT)

    # C1 chamfer on the four vertical corner edges
    chamfer(bp.edges().filter_by(Axis.Z), length=c1)

part = bp.part
export_step(part, "output.step")
