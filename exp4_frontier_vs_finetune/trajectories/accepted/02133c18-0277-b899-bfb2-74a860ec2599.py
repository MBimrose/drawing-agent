# 02133c18-0277-b899-bfb2-74a860ec2599 — agentic final (cand 1), IoU 0.901
from build123d import *

# ---- Dimensions read from the drawing (all mm) ----
plate_X = 90.0      # overall length, X (top view, bottom dim)
plate_Y = 70.0      # overall width, Y (right view, bottom dim)
plate_Z = 5.0       # plate thickness (front view)

x_hole1 = 15.0      # baseline dim: left hole column from -X edge
x_holeC = 45.0      # baseline dim: centre hole from -X edge (= plate_X/2)
x_hole2 = 75.0      # baseline dim: right hole column from -X edge
y_hole1 = 15.0      # baseline dim: front hole row from -Y edge
y_holeC = 35.0      # baseline dim: centre hole from -Y edge (= plate_Y/2)
y_hole2 = 55.0      # baseline dim: back hole row from -Y edge

dia_centre = 10.0   # ⌀10 THRU at plate centre
dia_corner = 6.0    # 4× ⌀6 THRU

cham = 0.5          # C0.5 chamfer on top & bottom outer edges

# ---- Derived positions relative to part centre ----
cx = plate_X / 2
cy = plate_Y / 2
corner_pts = [
    (x_hole1 - cx, y_hole1 - cy),
    (x_hole1 - cx, y_hole2 - cy),
    (x_hole2 - cx, y_hole1 - cy),
    (x_hole2 - cx, y_hole2 - cy),
]

with BuildPart() as bp:
    Box(plate_X, plate_Y, plate_Z)

    # C0.5 chamfers on the top and bottom perimeter edges only
    # (plan-view corners stay square, so vertical edges are excluded)
    horiz_edges = [e for e in bp.edges() if abs(e.tangent_at(0).Z) < 1e-3]
    chamfer(horiz_edges, length=cham)

    # ⌀10 THRU at centre
    with Locations((x_holeC - cx, y_holeC - cy)):
        Cylinder(radius=dia_centre / 2, height=plate_Z * 3, mode=Mode.SUBTRACT)

    # 4× ⌀6 THRU
    with Locations(corner_pts):
        Cylinder(radius=dia_corner / 2, height=plate_Z * 3, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
