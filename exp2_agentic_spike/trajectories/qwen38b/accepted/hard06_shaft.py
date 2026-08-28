# hard06_shaft — agentic final (cand 4), IoU 0.989
from build123d import *

# ---- dimensions read from the drawing (mm) ----
d_base = 42.0    # mm, base cylinder diameter   (Top: Ø42 THRU)
d_mid  = 30.0    # mm, middle cylinder diameter (Top: Ø30 THRU)
d_top  = 18.0    # mm, top cylinder diameter    (Top: Ø18)
h_base = 26.0    # mm, base step height         (Right view)
h_mid  = 21.0    # mm, middle step height       (Right view)
h_top  = 11.0    # mm, top step height          (Right / Front view)

# ---- derived values ----
H_total = h_base + h_mid + h_top   # 58 mm overall height (26 + 21 + 11)

# ---- three coaxial cylinders, stacked from z = 0 ----
# Each is centered on the origin then translated so its base sits on top
# of the previous step.
c_base = Cylinder(radius=d_base / 2, height=h_base, align=Align.CENTER).translate((0, 0, h_base / 2))
c_mid  = Cylinder(radius=d_mid / 2,  height=h_mid,  align=Align.CENTER).translate((0, 0, h_base + h_mid / 2))
c_top  = Cylinder(radius=d_top / 2,  height=h_top,  align=Align.CENTER).translate((0, 0, h_base + h_mid + h_top / 2))

# ---- union the three steps into one solid ----
part = c_base + c_mid + c_top

export_step(part, "output.step")
