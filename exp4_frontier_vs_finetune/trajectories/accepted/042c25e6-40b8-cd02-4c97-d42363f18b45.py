# 042c25e6-40b8-cd02-4c97-d42363f18b45 — agentic final (cand 1), IoU 0.954
from build123d import *

# --- parameters (all mm, read from drawing) ---
L = 60.0        # overall length X (top/front views)
W = 40.0        # overall depth Y (right view)
H = 20.0        # overall height Z (front/right views)
edge_r = 2.0    # 4x R2 called out in each of the 3 views -> all 12 box edges
hole_d = 6.0    # 4x ⌀6 THRU
hole_x1 = 15.0  # left hole column, from left edge
hole_x2 = 45.0  # right hole column, from left edge (60-45=15 symmetric)
hole_y1 = 10.0  # front hole row, from front edge
hole_y2 = 30.0  # back hole row, from front edge (40-30=10 symmetric)
# corner notch (front-left-bottom): no explicit dims on sheet, scaled from views
notch_x = 25.0  # notch extent in X from left (-X) face
notch_y = 15.0  # notch extent in Y from front (-Y) face
notch_z = 8.0   # notch height from bottom face

with BuildPart() as bp:
    # base block centered on origin
    Box(L, W, H)
    # R2 on all 12 edges (three "4x R2" notes, one per view)
    fillet(bp.edges(), radius=edge_r)
    # rectangular corner notch, open on -X face, -Y face and bottom face
    with Locations((-L / 2 + notch_x / 2,
                    -W / 2 + notch_y / 2,
                    -H / 2 + notch_z / 2)):
        Box(notch_x, notch_y, notch_z, mode=Mode.SUBTRACT)
    # 4x ⌀6 through-holes along Z
    hole_pts = [
        (hole_x1 - L / 2, hole_y1 - W / 2, 0.0),
        (hole_x1 - L / 2, hole_y2 - W / 2, 0.0),
        (hole_x2 - L / 2, hole_y1 - W / 2, 0.0),
        (hole_x2 - L / 2, hole_y2 - W / 2, 0.0),
    ]
    with Locations(hole_pts):
        Cylinder(radius=hole_d / 2, height=H + 2.0, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
