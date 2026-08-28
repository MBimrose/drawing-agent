# std06_shaft — agentic final (cand 1), IoU 0.993
from build123d import *

# ---- Named parameters (all mm, read from the drawing) ----
base_dia = 46.0   # mm  base flange OD  (Top Ø46 circle; Front & Right bottom width 46)
base_h   = 17.0   # mm  base flange thickness (Front/Right dim 17)
mid_dia  = 24.0   # mm  middle boss OD  (Top Ø24 circle; Right Ø24)
mid_h    = 28.0   # mm  middle boss height above base (Front/Right dim 28)
total_h  = 56.0   # mm  overall height (Front/Right dim 56)
pin_dia  = 14.0   # mm  top pin OD (Top Ø14 circle; Right Ø14)

# Derived: top pin height closes the chain 17 + 28 + pin_h = 56
pin_h = total_h - base_h - mid_h   # mm  = 56 - 17 - 28 = 11

base_r = base_dia / 2.0
mid_r  = mid_dia  / 2.0
pin_r  = pin_dia  / 2.0

with BuildPart() as builder:
    # Tier 1: base flange, z = 0 .. 17
    with Locations((0, 0, 0)):
        Cylinder(radius=base_r, height=base_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Tier 2: middle boss, z = 17 .. 45
    with Locations((0, 0, base_h)):
        Cylinder(radius=mid_r, height=mid_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Tier 3: top pin, z = 45 .. 56
    with Locations((0, 0, base_h + mid_h)):
        Cylinder(radius=pin_r, height=pin_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

part = builder.part
export_step(part, "output.step")
