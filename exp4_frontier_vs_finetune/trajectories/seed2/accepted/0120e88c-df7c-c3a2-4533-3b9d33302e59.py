# 0120e88c-df7c-c3a2-4533-3b9d33302e59 — agentic final (cand 1), IoU 1.000
from build123d import *

# ---------- dimensions read from the drawing ----------
plate_L = 80.0   # mm — overall length (X), top & front views
plate_W = 60.0   # mm — overall width (Y), right view
plate_T = 5.0    # mm — overall thickness (Z), front & right views

slot_l = 20.0    # mm — slot length (X), callout "2 x 20 x 2.5 DEEP"
slot_w = 2.0     # mm — slot width (Y)
slot_d = 2.5     # mm — slot depth from top face (blind)
slot_x = 40.0    # mm — slot centre from left edge (top view)
slot_y = 52.5    # mm — slot centre from front edge (right view)

c1 = 1.0         # mm — C1 (45°) chamfer on the four edges of the front face

with BuildPart() as bp:
    # base plate: X 0..80, Y 0..60, Z 0..5
    Box(plate_L, plate_W, plate_T, align=(Align.MIN, Align.MIN, Align.MIN))

    # blind slot milled into the top face (Z from plate_T-slot_d to plate_T)
    with Locations((slot_x, slot_y, plate_T)):
        Box(slot_l, slot_w, slot_d,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
            mode=Mode.SUBTRACT)

    # C1 chamfer on the front-face perimeter (the four edges lying at Y = 0)
    front_edges = [e for e in bp.edges() if abs(e.center().Y) < 1e-6]
    chamfer(front_edges, c1)

part = bp.part
export_step(part, "output.step")
