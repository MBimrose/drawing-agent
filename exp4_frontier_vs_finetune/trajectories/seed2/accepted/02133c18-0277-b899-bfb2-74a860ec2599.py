# 02133c18-0277-b899-bfb2-74a860ec2599 — agentic final (cand 1), IoU 0.901
from build123d import *

# ---- dimensions read from the drawing (mm) ----
plate_x = 90.0      # mm  overall X (top view bottom dim / front view)
plate_y = 70.0      # mm  overall Y (right view "70")
plate_t = 5.0       # mm  thickness (front/right view "5")

dim_x_left   = 15.0  # mm  left edge -> left hole column
dim_x_center = 45.0  # mm  left edge -> centre (= plate_x/2)
dim_x_right  = 75.0  # mm  left edge -> right hole column
dim_y_front  = 15.0  # mm  front edge -> front hole row
dim_y_center = 35.0  # mm  front edge -> centre (= plate_y/2)
dim_y_back   = 55.0  # mm  front edge -> back hole row

d_small = 6.0   # mm  4x dia-6 THRU
d_big   = 10.0  # mm  dia-10 THRU (centre)
cham    = 0.5   # mm  C0.5 chamfer on all exterior edges

# ---- derived ----
hole_x = (dim_x_right - dim_x_left) / 2.0   # (75-15)/2 = 30
hole_y = (dim_y_back - dim_y_front) / 2.0   # (55-15)/2 = 20
# consistency: (dim_x_left+dim_x_right)/2 == dim_x_center == plate_x/2
#              (dim_y_front+dim_y_back)/2 == dim_y_center == plate_y/2

with BuildPart() as bp:
    # base plate, centred in XY, sitting on Z=0
    Box(plate_x, plate_y, plate_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # C0.5 on every exterior edge (4 plan corners + top/bottom rims)
    chamfer(edges(), length=cham)

    # centre hole: dia 10 THRU
    with Locations((0.0, 0.0, plate_t / 2.0)):
        Cylinder(d_big / 2.0, plate_t + 4.0, mode=Mode.SUBTRACT)

    # 4x dia 6 THRU at (±30, ±20)
    pts = [( hole_x,  hole_y, plate_t / 2.0),
           ( hole_x, -hole_y, plate_t / 2.0),
           (-hole_x,  hole_y, plate_t / 2.0),
           (-hole_x, -hole_y, plate_t / 2.0)]
    with Locations(pts):
        Cylinder(d_small / 2.0, plate_t + 4.0, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
