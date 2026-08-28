# 0975cab6-f02f-e897-b6f6-449b7b9ace8e — agentic final (cand 1), IoU 0.996
from build123d import *

# ---- dimensions read from the drawing ----
plate_len = 80.0      # mm  overall length in X (top / front views)
plate_wid = 48.0      # mm  overall width in Y (right view)
plate_thk = 4.0       # mm  plate thickness in Z (front view)

pocket_len = 29.0     # mm  pocket length in X (callout "15 x 29 x 2 DEEP")
pocket_wid = 15.0     # mm  pocket width in Y  (callout)
pocket_dep = 2.0      # mm  pocket depth from top face (callout)

pocket_cx = 40.0      # mm  pocket centre from left edge (top view baseline dim)
pocket_cy = 20.0      # mm  pocket centre from front edge (right view dim)

hole_dia = 4.0        # mm  "2x D4 THRU"
hole_x1 = 32.5        # mm  first hole centre from left edge (top view)
hole_x2 = 55.0        # mm  second hole centre from left edge (top view)
hole_y = pocket_cy    # mm  holes lie on the pocket centreline

with BuildPart() as bp:
    # base plate, front-left-bottom corner at the origin
    Box(plate_len, plate_wid, plate_thk,
        align=(Align.MIN, Align.MIN, Align.MIN))

    # shallow rectangular pocket cut into the top face
    with Locations((pocket_cx, pocket_cy, plate_thk)):
        Box(pocket_len, pocket_wid, pocket_dep,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
            mode=Mode.SUBTRACT)

    # two through holes (second one breaks through the pocket end wall)
    with Locations((hole_x1, hole_y, 0.0),
                   (hole_x2, hole_y, 0.0)):
        Cylinder(radius=hole_dia / 2, height=plate_thk,
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
