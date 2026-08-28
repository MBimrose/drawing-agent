# std05_shaft — agentic final (cand 1), IoU 0.839
from build123d import *

# ---- named parameters (all dimensions read from the drawing) ----
d_base = 38   # mm  base flange OD   (Top view "⌀38"; Front/Right base width 38)
h_base = 26   # mm  base flange height (Front view 38x26 rectangle; Right view "26")
d_mid  = 24   # mm  middle boss OD   (Top view "⌀24")
h_mid  = 22   # mm  middle boss height (side-view chain "22")
d_top  = 16   # mm  top boss OD      (Top view "⌀16")
h_top  = 22   # mm  top boss height    (side-view chain "22")
# Z chain check: overall height = h_base + h_mid + h_top = 26 + 22 + 22 = 70 mm

# ---- derived values ----
r_base = d_base / 2
r_mid  = d_mid / 2
r_top  = d_top / 2
z_mid  = h_base            # top face of base flange
z_top  = h_base + h_mid    # top face of middle boss

with BuildPart() as bp:
    # base flange (axis = Z, bottom at z=0, centered in XY)
    Cylinder(radius=r_base, height=h_base,
             align=(Align.CENTER, Align.CENTER, Align.MIN))
    # middle boss, coaxial, sitting on the base
    with Locations((0, 0, z_mid)):
        Cylinder(radius=r_mid, height=h_mid,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # top boss, coaxial, sitting on the middle boss
    with Locations((0, 0, z_top)):
        Cylinder(radius=r_top, height=h_top,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

part = bp.part
export_step(part, "output.step")
