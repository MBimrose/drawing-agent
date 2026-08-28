# std06_shaft — agentic final (cand 6), IoU 0.944
# Bearing block - three-tier cylindrical stack
import build123d as b
from build123d import *

# Dimensions read from the drawing
d_base = 48.0   # mm, base flange diameter (Top view outer circle)
d_mid  = 24.0   # mm, middle cylinder diameter (Top view middle circle)
d_top  = 14.0   # mm, top cylinder diameter (Top view inner circle)

h_base = 17.0   # mm, base flange height (Right view)
h_mid  = 29.0   # mm, middle cylinder height (Right view)
h_top  = 10.0   # mm, top cylinder height (Right view)

# Derived values
h_total = h_base + h_mid + h_top   # 56 mm, matches overall dimension

# Each cylinder: centered in X/Y, base at local z=0, then lifted in Z
cyl_align = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as part:
    # Base flange at origin
    Cylinder(d_base / 2.0, h_base, align=cyl_align)
    # Middle cylinder stacked on base (base at z = h_base)
    with Locations((0, 0, h_base)):
        Cylinder(d_mid / 2.0, h_mid, align=cyl_align)
    # Top cylinder stacked on middle (base at z = h_base + h_mid)
    with Locations((0, 0, h_base + h_mid)):
        Cylinder(d_top / 2.0, h_top, align=cyl_align)

# Export the finished solid (part.part is the resulting Part/Shape)
export_step(part.part, "output.step")
