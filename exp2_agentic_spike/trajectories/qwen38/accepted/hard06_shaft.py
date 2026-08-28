# hard06_shaft — agentic final (cand 4), IoU 0.989
from build123d import *

# --- dimensions read from the drawing ---
d_bottom = 42.0    # mm, bottom cylinder OD (Top view outer circle)
d_mid    = 30.0    # mm, middle cylinder OD (Top view middle circle)
d_top    = 18.0    # mm, top cylinder OD (Top view inner circle)
h_bottom = 26.0    # mm, bottom cylinder height (Front/Right views)
h_mid    = 21.0    # mm, middle cylinder height
h_top    = 11.0    # mm, top cylinder height

# --- derived values ---
h_total = h_bottom + h_mid + h_top   # 58 mm overall height (26 + 21 + 11)

# --- build the solid: three coaxial cylinders stacked on the Z axis ---
# align MIN in Z puts each cylinder's base on its Locations point, so the
# steps sit exactly on top of one another (face-to-face) and fuse into one solid.
with BuildPart() as bp:
    Cylinder(d_bottom / 2, h_bottom,
             align=(Align.CENTER, Align.CENTER, Align.MIN))                       # base Z = 0
    with Locations((0, 0, h_bottom)):
        Cylinder(d_mid / 2, h_mid,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))                    # base Z = 26
    with Locations((0, 0, h_bottom + h_mid)):
        Cylinder(d_top / 2, h_top,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))                    # base Z = 47

# bind the finished (unioned) solid to `part`
part = bp.part

export_step(part, "output.step")
