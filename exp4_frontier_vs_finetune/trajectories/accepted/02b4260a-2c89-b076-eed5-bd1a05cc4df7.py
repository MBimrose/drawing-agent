# 02b4260a-2c89-b076-eed5-bd1a05cc4df7 — agentic final (cand 1), IoU 1.000
from build123d import *

# ---------- dimensions read from the drawing ----------
L = 80.0            # mm  overall length (X), top/front views
W = 60.0            # mm  overall width (Y), right side view
T = 7.0             # mm  plate thickness (Z), front view

hole_dia = 5.0      # mm  8x D5 THRU (2x4)
col_pitch = 20.0    # mm  3x 20 between the 4 hole columns
row_pitch = 30.0    # mm  1x 30 between the 2 hole rows
col_margin = 10.0   # mm  left edge to first column
row_margin = 15.0   # mm  edge to first row (right side view)

pocket_dia = 30.0   # mm  D30 central blind pocket
pocket_depth = 2.0  # mm  pocket depth (blind, from top)

edge_chamfer = 0.5  # mm  C0.5 on the four vertical corners

# derived hole coordinates (base sketch is centered on the origin)
xs = [col_margin + i * col_pitch - L / 2 for i in range(4)]   # -30,-10,10,30
ys = [row_margin + j * row_pitch - W / 2 for j in range(2)]   # -15, 15

with BuildPart() as bp:
    # base plate
    with BuildSketch():
        Rectangle(L, W)
    extrude(amount=T)

    top = Plane.XY.offset(T)

    # central D30 x 2 deep blind pocket (from top face)
    with BuildSketch(top):
        Circle(pocket_dia / 2)
    extrude(amount=-pocket_depth, mode=Mode.SUBTRACT)

    # eight D5 through holes, 4 columns x 2 rows
    with BuildSketch(top):
        with Locations([(x, y) for x in xs for y in ys]):
            Circle(hole_dia / 2)
    extrude(amount=-T, mode=Mode.SUBTRACT)

    # C0.5 chamfers on the four vertical corner edges
    chamfer(bp.edges().filter_by(Axis.Z), edge_chamfer)

part = bp.part
export_step(part, "output.step")
