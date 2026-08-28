# hard02_notchplate — agentic final (cand 1), IoU 0.989
from build123d import *

# --- dimensions read from the drawing (mm) ---
seg_left   = 27   # mm  X chain segment 1 (full-depth left part)
notch_w    = 20   # mm  X chain segment 2 (front notch width)
seg_right  = 31   # mm  X chain segment 3 (full-depth right part)
W = seg_left + notch_w + seg_right   # mm  overall X = 27 + 20 + 31 = 78

D          = 53   # mm  overall Y (Top left dim = Right view length)
T          = 15   # mm  plate thickness Z (Right view 53 x 15)
notch_d    = 16   # mm  notch depth in from the front edge (Top view "16")

hole_d     = 10   # mm  2X Ø10 THRU
hole_r     = hole_d / 2
hole_margin = 16  # mm  hole centers are 16 in from side edges and back edge (Top view)
hole_y     = D - hole_margin        # = 37
hole_x1    = hole_margin            # = 16
hole_x2    = W - hole_margin        # = 62

with BuildPart() as bp:
    # base plate: X[0..78], Y[0..53], Z[0..15]
    Box(W, D, T, align=(Align.MIN, Align.MIN, Align.MIN))

    # front notch: X[27..47], Y[0..16], through full thickness
    # (tool protrudes 1 mm past the open front face for a clean cut; effective depth = notch_d)
    with Locations((seg_left, -1, 0)):
        Box(notch_w, notch_d + 1, T,
            align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.SUBTRACT)

    # two through holes
    with Locations((hole_x1, hole_y, 0), (hole_x2, hole_y, 0)):
        Cylinder(radius=hole_r, height=T,
                 align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
