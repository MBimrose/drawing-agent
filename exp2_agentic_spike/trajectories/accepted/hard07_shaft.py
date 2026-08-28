# hard07_shaft — agentic final (cand 1), IoU 0.942
from build123d import *

# ---- dimensions read from the drawing ----
d_base = 42.0   # mm  base tier diameter (Top outer circle / Front & Right bottom width)
d_mid  = 22.0   # mm  middle tier diameter (Top middle circle)
d_top  = 16.0   # mm  top tier diameter (Top inner circle)
h_base = 28.0   # mm  bottom segment of vertical chain (Front & Right)
h_mid  = 18.0   # mm  middle segment of vertical chain
h_top  = 13.0   # mm  top segment of vertical chain

# derived overall height: 28 + 18 + 13 = 59
H_total = h_base + h_mid + h_top  # mm

with BuildPart() as bp:
    # base tier, z = 0 .. h_base
    with Locations((0, 0, 0)):
        Cylinder(radius=d_base / 2, height=h_base,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # middle tier, z = h_base .. h_base+h_mid
    with Locations((0, 0, h_base)):
        Cylinder(radius=d_mid / 2, height=h_mid,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # top tier, z = h_base+h_mid .. H_total
    with Locations((0, 0, h_base + h_mid)):
        Cylinder(radius=d_top / 2, height=h_top,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

part = bp.part
export_step(part, "output.step")
