# 0e134a30-6dfe-a1ae-559b-5c75fec1f359 — agentic final (cand 1), IoU 0.912
from build123d import *

# ---- Named parameters (read from drawing) ----
L = 80.0              # mm  overall length (X) - top/front views
W = 60.0              # mm  overall width  (Y) - top/right views
H = 15.0              # mm  overall height (Z) - front view

POCKET_L = 70.0       # mm  recess length (X) - "50 x 70 x 4 DEEP"
POCKET_W = 50.0       # mm  recess width  (Y) - "50 x 70 x 4 DEEP"
POCKET_D = 4.0        # mm  recess depth      - "50 x 70 x 4 DEEP"

BOSS_L = 30.0         # mm  central pad length (X) - top view
BOSS_W = 16.0         # mm  central pad width  (Y) - top view
BOSS_H = POCKET_D     # mm  pad stands on pocket floor, top flush with top face

HOLE_D = 5.0          # mm  "4x D5 THRU"
HOLE_X1 = 20.0        # mm  left  hole column centre from left edge
HOLE_X2 = 60.0        # mm  right hole column centre from left edge
HOLE_Y1 = 15.0        # mm  front hole row centre from front edge
HOLE_Y2 = 45.0        # mm  back  hole row centre from front edge

# ---- Derived values ----
hole_xs = (HOLE_X1 - L / 2, HOLE_X2 - L / 2)   # -20, +20 (centred pattern)
hole_ys = (HOLE_Y1 - W / 2, HOLE_Y2 - W / 2)   # -15, +15 (centred pattern)
z_floor = H - POCKET_D                          # pocket floor at z = 11

with BuildPart() as model:
    # Base plate 80 x 60 x 15
    Box(L, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Centred rectangular pocket, 4 deep from the top face
    with Locations((0, 0, H)):
        Box(POCKET_L, POCKET_W, POCKET_D,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
            mode=Mode.SUBTRACT)

    # Central island pad on the pocket floor, flush with the top face
    with Locations((0, 0, z_floor)):
        Box(BOSS_L, BOSS_W, BOSS_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

    # 4x D5 through holes
    with Locations([(x, y) for x in hole_xs for y in hole_ys]):
        Cylinder(radius=HOLE_D / 2, height=H,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = model.part
export_step(part, "output.step")
