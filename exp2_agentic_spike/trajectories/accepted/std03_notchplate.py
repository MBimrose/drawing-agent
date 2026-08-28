# std03_notchplate — agentic final (cand 2), IoU 0.970
from build123d import *

# ---------- dimensions read from the drawing ----------
seg_left  = 22.0   # mm  left segment of X chain
notch_w   = 30.0   # mm  middle segment of X chain (notch width)
seg_right = 49.0   # mm  right segment of X chain
L = seg_left + notch_w + seg_right   # mm  overall X = 22 + 30 + 49 = 101
W = 54.0           # mm  overall depth (Y)
T = 14.0           # mm  thickness (Z)
notch_d = 18.0     # mm  notch depth from the front (-Y) edge
hole_d  = 6.0      # mm  2X Ø6 THRU
hole_x  = 16.0     # mm  hole center from each side edge (symmetric about L/2)
hole_y  = 18.0     # mm  hole center from the back (+Y) edge

with BuildPart() as bp:
    # base plate, min corner at origin
    Box(L, W, T, align=(Align.MIN, Align.MIN, Align.MIN))

    # rectangular notch open at the front edge, through full thickness
    with Locations((seg_left, 0, 0)):
        Box(notch_w, notch_d, T,
            align=(Align.MIN, Align.MIN, Align.MIN),
            mode=Mode.SUBTRACT)

    # two through holes (base at z=0, full thickness -> THRU)
    with Locations((hole_x, W - hole_y, 0),
                   (L - hole_x, W - hole_y, 0)):
        Cylinder(radius=hole_d / 2, height=T,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
