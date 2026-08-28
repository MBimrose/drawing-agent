# hard03_notchplate — agentic final (cand 1), IoU 0.975
from build123d import *

# ---- dimensions read from the drawing ----
seg_left  = 24   # mm  X: left edge -> notch left side
seg_notch = 20   # mm  X: notch width (middle segment)
seg_right = 28   # mm  X: notch right side -> right edge
depth     = 54   # mm  overall Y (Top left dim = Right view length)
thick     = 14   # mm  overall Z (Front and Right views)
notch_dep = 16   # mm  Y depth of the front notch (through full thickness)
hole_dia  = 8    # mm  2X Ø8 THRU
hole_x_in = 14   # mm  hole centre inset from left/right side edges (symmetric)
hole_y    = 44   # mm  hole centre Y (both holes on one line near the back edge)

width = seg_left + seg_notch + seg_right   # 24 + 20 + 28 = 72 mm overall X

with BuildPart() as builder:
    # base plate, min corner at origin
    Box(width, depth, thick, align=(Align.MIN, Align.MIN, Align.MIN))

    # front notch: middle X segment (x = seg_left .. seg_left+seg_notch),
    # from the front edge (y=0) back by notch_dep, through the full thickness
    with Locations((seg_left, 0, 0)):
        Box(seg_notch, notch_dep, thick,
            align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.SUBTRACT)

    # 2X Ø8 through holes (symmetric about the X centreline)
    with Locations((hole_x_in, hole_y, thick / 2),
                   (width - hole_x_in, hole_y, thick / 2)):
        Cylinder(radius=hole_dia / 2, height=thick, mode=Mode.SUBTRACT)

part = builder.part
export_step(part, "output.step")
