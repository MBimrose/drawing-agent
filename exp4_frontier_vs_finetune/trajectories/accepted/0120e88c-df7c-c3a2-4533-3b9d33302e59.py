# 0120e88c-df7c-c3a2-4533-3b9d33302e59 — agentic final (cand 2), IoU 0.992
from build123d import *

# ---- dimensions read from the drawing ----
plate_x = 80.0       # mm  overall length (front & top views)
plate_y = 60.0       # mm  overall depth (right side view, overall "60")
plate_z = 5.0        # mm  plate thickness (front view "5")
edge_chamfer = 1.0   # mm  C1 chamfer on the plate edges
                     #     (plan callouts at the corners -> vertical corner edges;
                     #      front view callouts top & bottom -> top/bottom perimeter edges)

slot_wid = 2.0       # mm  recess width along Y  (callout "2 x ...")
slot_len = 20.0      # mm  recess length along X (callout "... x 20 x ...")
slot_depth = 2.5     # mm  recess depth          (callout "... 2.5 DEEP")
slot_cx = 40.0       # mm  slot centre from left edge (top view) = plate_x/2
slot_cy = 52.5       # mm  slot centre from front edge (right side view)

with BuildPart() as bp:
    # base plate, front-left-bottom corner at the origin
    Box(plate_x, plate_y, plate_z,
        align=(Align.MIN, Align.MIN, Align.MIN))

    # C1 on ALL outer edges of the plate:
    # 8 top/bottom perimeter edges + 4 vertical corner edges
    chamfer(bp.edges(), edge_chamfer)

    # blind rectangular slot on the top face (sharp edges, cut after chamfer)
    with Locations((slot_cx, slot_cy, plate_z - slot_depth)):
        Box(slot_len, slot_wid, slot_depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
