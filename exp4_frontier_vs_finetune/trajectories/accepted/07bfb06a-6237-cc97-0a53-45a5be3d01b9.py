# 07bfb06a-6237-cc97-0a53-45a5be3d01b9 — agentic final (cand 3), IoU 0.942
from build123d import *

# ---- named dimensions read from the drawing (mm) ----
LX = 80            # mm  overall X (top view & front view)
LY = 60            # mm  overall Y (right side view)
LZ = 6             # mm  plate thickness (front & right views)
R_CORNER = 2       # mm  "4x R2" fillet on the four plan corners

POCKET_X = 24      # mm  left margin to pocket (chain 24 + 32 + 24 = 80)
POCKET_W = 32      # mm  pocket width in X
POCKET_H = 15      # mm  pocket height in Y
POCKET_CY = 29     # mm  feature centerline, from bottom edge
POCKET_Y0 = POCKET_CY - POCKET_H / 2   # mm  pocket bottom edge = 21.5

TAB_D = 4          # mm  rounded-tab width in Y (dim "4")
TAB_R = TAB_D / 2  # mm  tab radius = 2; leftmost point X = 24 - 2 = 22 (dim "22")

# cutting tools built OUTSIDE the part context as pre-positioned solids
# (avoids any location being applied twice by a builder context)
pocket_tool = Pos(POCKET_X, POCKET_Y0, -1) * Box(
    POCKET_W, POCKET_H, LZ + 2, align=(Align.MIN, Align.MIN, Align.MIN)
)  # X 24..56, Y 21.5..36.5, Z -1..7 (through)
tab_tool = Pos(POCKET_X, POCKET_CY, -1) * Cylinder(
    TAB_R, LZ + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)
)  # dia-4 cylinder at (24,29); only its left semicircle protrudes past the pocket

with BuildPart() as bp:
    # base plate X:0..80, Y:0..60, Z:0..6
    Box(LX, LY, LZ, align=(Align.MIN, Align.MIN, Align.MIN))

    # fillet only the four outer vertical corner edges (R2) BEFORE cutting,
    # so no internal pocket wall can be filleted (a box has exactly 4 Z-parallel edges)
    fillet(bp.edges().filter_by(Axis.Z), radius=R_CORNER)

    # through-cut: rectangular pocket + rounded tab (union of the two removals)
    add(pocket_tool, mode=Mode.SUBTRACT)
    add(tab_tool, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
