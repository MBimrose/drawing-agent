# std00_steps3 — agentic final (cand 1), IoU 1.000
from build123d import *

# --- Dimensions read from the drawing ---
seg1_w = 19        # mm - left (tallest) step length along X
seg2_w = 37        # mm - middle step length along X
seg3_w = 29        # mm - right (lowest) step length along X
depth  = 31        # mm - part depth along Y (Top / Right views)
h1     = 34        # mm - overall height = left step height (Front / Right views)
drop23 = 15        # mm - drop from middle step top to right step top
h3     = 11        # mm - right (lowest) step height

# --- Derived values ---
h2 = h3 + drop23               # 26 mm - middle step height
W  = seg1_w + seg2_w + seg3_w  # 85 mm - overall length along X

with BuildPart() as bp:
    with Locations((0, 0, 0)):
        Box(seg1_w, depth, h1, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((seg1_w, 0, 0)):
        Box(seg2_w, depth, h2, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((seg1_w + seg2_w, 0, 0)):
        Box(seg3_w, depth, h3, align=(Align.MIN, Align.MIN, Align.MIN))

part = bp.part
export_step(part, "output.step")
