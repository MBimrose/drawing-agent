# 08ceb60e-09e1-b2d4-d0e2-af718c90dfc8 — agentic final (cand 2), IoU 0.955
from build123d import *

# ---------------- dimensions read from the drawing ----------------
W = 80            # mm  overall width  (X) - top & front views
D = 60            # mm  overall depth  (Y) - right view
H = 30            # mm  overall height (Z) - front view

POCKET_W = 40     # mm  recess width (X) - top view (20 -> 60, centred)
POCKET_D = 30     # mm  recess depth (Y) - top view (15 -> 45, centred)
POCKET_Z = 15     # mm  recess depth from top face - hidden lines in front/right views

HOLE_D = 6        # mm  "2x Ø6 THRU"
HOLE_X1 = 25      # mm  left hole centre from left face  - top view
HOLE_X2 = 55      # mm  right hole centre from left face - top view
HOLE_Y = D / 2    # mm  holes centred front-to-back (=30)

FILLET_R = 2      # mm  "6x R2": 4 outer edges // X + 2 recess-mouth edges // X

with BuildPart() as bp:
    # base block, centred on origin
    Box(W, D, H)

    # blind rectangular recess in the top face, centred in X and Y
    with Locations((0, 0, H / 2 - POCKET_Z / 2)):
        Box(POCKET_W, POCKET_D, POCKET_Z, mode=Mode.SUBTRACT)

    # two vertical through-holes
    with Locations((HOLE_X1 - W / 2, HOLE_Y - D / 2, 0),
                   (HOLE_X2 - W / 2, HOLE_Y - D / 2, 0)):
        Cylinder(radius=HOLE_D / 2, height=H, mode=Mode.SUBTRACT)

    # 6x R2: filter_by(Axis.X) yields only straight edges parallel to X;
    # the six wanted edges (outer top/bottom front/back + recess mouth
    # front/back) are exactly those whose centre lies at |z| = H/2
    targets = [
        e for e in bp.edges().filter_by(Axis.X)
        if abs(abs(e.center().Z) - H / 2) < 1e-3
    ]
    fillet(targets, radius=FILLET_R)

part = bp.part
export_step(part, "output.step")
