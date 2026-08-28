# 0264f04e-9879-24a1-30c7-74b898c39e5c — agentic final (cand 1), IoU 0.965
from build123d import *

# ---------------------------------------------------------------------------
# Dimensions read from the drawing (all mm)
# ---------------------------------------------------------------------------
base_dia = 60.0   # base flange diameter  (front view "⌀60"; plan "30" = radius)
base_ht  = 15.0   # base flange thickness (front view vertical chain)
mid_dia  = 40.0   # middle step diameter  (front view "⌀40")
mid_ht   = 15.0   # middle step height    (front view vertical chain)
boss_dia = 24.0   # top boss diameter     (front view "⌀24")
boss_ht  = 20.0   # top boss height       (front view vertical chain)
hole_dia = 5.0    # hole diameter         (callout "2x ⌀5 THRU")
hole_pcd = 50.0   # hole pitch-circle dia (side view "50" between hole hidden lines)

# Derived values
total_ht = base_ht + mid_ht + boss_ht   # overall height: 15 + 15 + 20 = 50
hole_rad = hole_pcd / 2                 # holes at r = 25, on the plan's vertical axis

with BuildPart() as builder:
    # Base flange
    with BuildSketch():
        Circle(base_dia / 2)
    extrude(amount=base_ht)

    # Middle step
    with BuildSketch(Plane.XY.offset(base_ht)):
        Circle(mid_dia / 2)
    extrude(amount=mid_ht)

    # Top boss
    with BuildSketch(Plane.XY.offset(base_ht + mid_ht)):
        Circle(boss_dia / 2)
    extrude(amount=boss_ht)

    # 2x ⌀5 THRU holes on the Y axis (top & bottom in plan view)
    with Locations((0, +hole_rad, 0), (0, -hole_rad, 0)):
        Cylinder(radius=hole_dia / 2, height=total_ht,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = builder.part
export_step(part, "output.step")
