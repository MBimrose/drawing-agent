# 082d1e48-2084-f5e6-e02a-5dde5f72e9df — agentic final (cand 1), IoU 0.991
from build123d import *

# ---- Dimensions read from the drawing ----
L = 80              # mm  overall length in X (top & front views)
W = 50              # mm  overall depth in Y (right view)
H = 30              # mm  overall height in Z (front & right views)
EDGE_R = 2          # mm  "4x R2" fillets on the four vertical edges

POCKET_X_OFF = 15   # mm  pocket offset from each X end (front chain: 15+50+15 = 80)
POCKET_Y_OFF = 10   # mm  pocket offset from each Y side (right chain: 10+30+10 = 50)
POCKET_DEPTH = 24   # mm  pocket depth from top face ("30 x 50 x 24 DEEP")
POCKET_L = L - 2 * POCKET_X_OFF   # mm = 50, matches callout
POCKET_W = W - 2 * POCKET_Y_OFF   # mm = 30, matches callout

HOLE_D = 8          # mm  "Ø8 THRU", axis along X
HOLE_Y = 25         # mm  hole centre from Y edge (right view) -> centred on 50
HOLE_Z = 15         # mm  hole centre height (right view)

with BuildPart() as bp:
    # Base block, centred in X/Y, bottom face on Z=0
    Box(L, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # 4x R2 on the vertical edges
    fillet(bp.edges().filter_by(Axis.Z), radius=EDGE_R)

    # Rectangular pocket from the top face, centred in X and Y
    with Locations((0, 0, H)):
        Box(POCKET_L, POCKET_W, POCKET_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
            mode=Mode.SUBTRACT)

    # Ø8 through hole along X (slightly over-length to guarantee a clean thru cut)
    with Locations((0, HOLE_Y - W / 2, HOLE_Z)):
        Cylinder(radius=HOLE_D / 2, height=L + 2,
                 rotation=(0, 90, 0), mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
