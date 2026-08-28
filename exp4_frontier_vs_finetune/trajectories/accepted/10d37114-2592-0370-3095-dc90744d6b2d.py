# 10d37114-2592-0370-3095-dc90744d6b2d — agentic final (cand 1), IoU 0.992
from build123d import *

# ---- Dimensions read from the drawing ----
outer_dia    = 60.0   # mm  overall diameter (front view ⌀60; right view 30 = edge->centerline)
height       = 60.0   # mm  overall height (front view)
step_up      = 45.0   # mm  bottom face -> counterbore floor (front view)
cbore_dia    = 50.0   # mm  counterbore diameter (front view ⌀50)
thru_dia     = 30.0   # mm  through-hole diameter (front view ⌀30)
hole_dia     = 5.0    # mm  small holes, callout "2x ⌀5 THRU"
edge_to_hole = 10.0   # mm  outer edge -> hole centre (top view)
# top-view chain check: 10 + 50 = 60 = outer_dia  =>  hole centre to far edge = 50

outer_r     = outer_dia / 2
cbore_r     = cbore_dia / 2
thru_r      = thru_dia / 2
hole_r      = hole_dia / 2
cbore_depth = height - step_up          # 15 mm
hole_offset = outer_r - edge_to_hole    # 20 mm -> holes at x = +/-20

with BuildPart() as bp:
    # base cylinder ⌀60 x 60
    Cylinder(radius=outer_r, height=height,
             align=(Align.CENTER, Align.CENTER, Align.MIN))
    # counterbore ⌀50 from the top face down to z = 45
    with Locations((0, 0, step_up)):
        Cylinder(radius=cbore_r, height=cbore_depth,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)
    # ⌀30 through hole
    Cylinder(radius=thru_r, height=height,
             align=(Align.CENTER, Align.CENTER, Align.MIN),
             mode=Mode.SUBTRACT)
    # 2x ⌀5 through holes on the X axis
    with Locations((hole_offset, 0), (-hole_offset, 0)):
        Cylinder(radius=hole_r, height=height,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
