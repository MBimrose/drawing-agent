# 0b611efc-c103-5519-6650-76d8117ad50e — agentic final (cand 1), IoU 1.000
from build123d import *

# ---- Dimensions read from the drawing (all mm) ----
len_x = 64        # overall X extent (top & front views)
len_y = 80        # overall Y extent (right view)
arm_w = 12        # arm width: leg width in X (front view) = bar width in Y (right view)
thk = 8           # part thickness (front & right views)

poc_x = 6         # pocket size along X  (callout: 6 x 10 x 7 DEEP)
poc_y = 10        # pocket size along Y  (callout)
poc_depth = 7     # pocket depth from top face (callout)
poc_cx = 38       # pocket centre X, from left edge (top view)
poc_cy = 74       # pocket centre Y, from front edge (right view) = 80 - 12/2 (arm centreline)

with BuildPart() as bp:
    # Arm along X (back bar): x 0..64, y 68..80, z 0..8
    with Locations((len_x / 2, len_y - arm_w / 2, thk / 2)):
        Box(len_x, arm_w, thk)
    # Arm along Y (left leg): x 0..12, y 0..80, z 0..8
    with Locations((arm_w / 2, len_y / 2, thk / 2)):
        Box(arm_w, len_y, thk)
    # Blind pocket from the top face: 6 x 10, 7 deep (1 mm floor remains)
    with Locations((poc_cx, poc_cy, thk - poc_depth / 2)):
        Box(poc_x, poc_y, poc_depth, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
