# hard08_lbracket — agentic final (cand 2), IoU 1.000
from build123d import *

# ---- Dimensions read from drawing (mm) ----
wall_thk = 12          # mm, vertical wall thickness (Front: "12")
base_len = 68          # mm, base length from wall inner face to free end (Top/Front: "68")
width = 46             # mm, part width in Y (Top/Right: "46")
base_thk = 12          # mm, base plate thickness (Front/Right: "12")
wall_ht = 51           # mm, wall height above top of base (Front/Right: "51")
hole_dia = 7           # mm, through-hole diameter in base (Top: "⌀7")
hole_from_end = 19     # mm, hole center from free end of base (read from Top/Front views)

# ---- Derived values ----
total_len = wall_thk + base_len        # 12 + 68 = 80 mm overall X
total_ht = base_thk + wall_ht          # 12 + 51 = 63 mm overall Z
hole_x = total_len - hole_from_end     # 61 mm from wall outer face
hole_y = width / 2                     # 23 mm, centered across width

with BuildPart() as bp:
    # Base plate: full footprint, 12 thick
    Box(total_len, width, base_thk, align=(Align.MIN, Align.MIN, Align.MIN))
    # Vertical wall at the X=0 end, full width, rising 51 above the base
    with Locations((0, 0, base_thk)):
        Box(wall_thk, width, wall_ht, align=(Align.MIN, Align.MIN, Align.MIN))
    # ⌀7 through-hole vertically through the full base thickness
    with Locations((hole_x, hole_y, 0)):
        Cylinder(radius=hole_dia / 2, height=base_thk,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
