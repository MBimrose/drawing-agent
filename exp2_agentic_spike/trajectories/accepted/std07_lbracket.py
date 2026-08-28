# std07_lbracket — agentic final (cand 1), IoU 0.869
from build123d import *

# ---------- dimensions read from the drawing ----------
base_len  = 83.0   # mm  overall length in X (Top / Front)
base_wid  = 40.0   # mm  overall depth in Y (Top / Right)
total_h   = 60.0   # mm  overall height in Z (Front / Right)
wall_h    = 46.0   # mm  wall height above base top (Front / Right)
wall_thk  = 11.0   # mm  wall thickness in X (Front chain: 83 - 72)
hole_d    = 8.0    # mm  through-hole diameter (Top callout Ø8)
hole_x    = 64.0   # mm  hole centre from the wall end (read from Top view)
hole_y    = 20.0   # mm  hole centre, centred in the 40 mm depth

# ---------- derived values ----------
base_thk  = total_h - wall_h      # 14 mm base thickness (60 - 46)
exposed   = base_len - wall_thk   # 72 mm, matches the drawing chain 11 + 72 = 83

with BuildPart() as bp:
    # base slab, corner at origin
    Box(base_len, base_wid, base_thk, align=(Align.MIN, Align.MIN, Align.MIN))

    # vertical wall at the X = 0 end, full depth, on top of the base
    with Locations((0, 0, base_thk)):
        Box(wall_thk, base_wid, wall_h, align=(Align.MIN, Align.MIN, Align.MIN))

    # Ø8 through hole in the base plate
    with Locations((hole_x, hole_y, -1)):
        Cylinder(radius=hole_d / 2, height=base_thk + 2,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
