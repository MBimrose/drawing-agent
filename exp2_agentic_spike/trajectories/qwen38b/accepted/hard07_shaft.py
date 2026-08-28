# hard07_shaft — agentic final (cand 2), IoU 1.000
from build123d import *

# ---- Dimensions read from the drawing (mm) ----
d_base = 42.0   # mm, base cylinder diameter (Top view outer circle)
h_base = 26.0   # mm, base step height (Right view, bottom segment)
d_mid  = 22.0   # mm, middle cylinder diameter (Top view middle circle)
h_mid  = 18.0   # mm, middle step height (Right view, middle segment)
d_top  = 16.0   # mm, top cylinder diameter (Top view inner circle)
h_top  = 13.0   # mm, top step height (Right view, top segment)

# Derived
h_total = h_base + h_mid + h_top   # 26 + 18 + 13 = 57 mm overall height

# ---- Build the stepped solid cylinder ----
with BuildPart() as p:
    # Base step, bottom face at z = 0
    Cylinder(d_base / 2, h_base, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Middle step, sitting on the base
    with Locations((0, 0, h_base)):
        Cylinder(d_mid / 2, h_mid, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Top step, sitting on the middle step
    with Locations((0, 0, h_base + h_mid)):
        Cylinder(d_top / 2, h_top, align=(Align.CENTER, Align.CENTER, Align.MIN))

part = p.part
export_step(part, "output.step")
