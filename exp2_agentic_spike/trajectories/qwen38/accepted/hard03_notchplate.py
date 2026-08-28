# hard03_notchplate — agentic final (cand 2), IoU 1.000
from build123d import *

# ---- dimensions read from the drawing (mm) ----
w1 = 24.0            # left segment (left edge -> notch left wall)
w2 = 20.0            # notch width
w3 = 28.0            # right segment (notch right wall -> right edge)
W = w1 + w2 + w3     # overall width = 72
D = 54.0             # overall depth
T = 14.0             # plate thickness
notch_depth = 16.0   # notch depth from front edge
hole_d = 8.0         # hole diameter
hole_inset_x = 12.0  # hole inset from left/right edges
hole_inset_top = 12.0  # hole inset from top (back) edge

# derived hole centre positions
hole_y = D - hole_inset_top          # 42
hole_x_left = hole_inset_x           # 12
hole_x_right = W - hole_inset_x      # 60

with BuildPart() as bp:
    # base plate, origin at front-left-bottom
    Box(W, D, T, align=(Align.MIN, Align.MIN, Align.MIN))
    # front-edge notch (through thickness)
    with Locations((w1, 0, 0)):
        Box(w2, notch_depth, T, align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.SUBTRACT)
    # two through holes
    with Locations((hole_x_left, hole_y, 0), (hole_x_right, hole_y, 0)):
        Cylinder(hole_d / 2, T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
