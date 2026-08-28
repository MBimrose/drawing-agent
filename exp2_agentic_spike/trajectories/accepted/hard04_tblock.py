# hard04_tblock — agentic final (cand 1), IoU 1.000
from build123d import *

# ---- named parameters (dimensions read from the drawing) ----
thickness = 12   # mm  part height (Z): Front "12" = Right "12" (only vertical size)
leg_y     = 34   # mm  front-leg length (Y): Top "34" = Right "34"
arm_y     = 17   # mm  rear-arm depth (Y):  Top "17" = Right "17"
overhang  = 23   # mm  arm margin beside leg (X): Top/Front "23" (left; right equal by symmetry)
leg_x     = 25   # mm  front-leg width (X):  Top/Front "25"

# ---- derived overall extents (explicit dimension chains) ----
total_x = overhang + leg_x + overhang   # X: 23 + 25 + 23 = 71 mm (leg centred on arm)
total_y = leg_y + arm_y                 # Y: 34 + 17 = 51 mm

# key coordinates of the T footprint
x0 = 0.0
x1 = overhang            # 23  left side of leg
x2 = overhang + leg_x    # 48  right side of leg
x3 = total_x             # 71  right end of arm
y0 = 0.0                 # front face of leg
y1 = leg_y               # 34  front face of arm / rear of leg
y2 = total_y             # 51  rear face of arm

pts = [
    (x0, y1), (x1, y1),   # front edge of left arm overhang
    (x1, y0), (x2, y0),   # left side then front face of the leg
    (x2, y1), (x3, y1),   # right side of leg then front edge of right overhang
    (x3, y2), (x0, y2),   # right end then rear edge of the arm
]

with BuildPart() as bp:
    with BuildSketch():                 # XY plane -> Top view
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    extrude(amount=thickness)           # +Z, height 12

part = bp.part
export_step(part, "output.step")
