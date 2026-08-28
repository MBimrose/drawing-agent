# 00874eac-be8c-17f8-ad7b-6a035b6c40ae — agentic final (cand 1), IoU 0.998
from build123d import *

# ---- dimensions read from the drawing ----
L = 80          # mm overall length (X), TOP view
W = 60          # mm overall width  (Y), RIGHT view
H = 30          # mm overall height (Z), FRONT view
wall = 2        # mm side-wall thickness ("2" callouts)
cavity_h = 28   # mm inner cavity height (FRONT "28"); top plate = H - cavity_h = 2
hole_d = 4      # mm "4x Ø4 THRU"
hole_x1 = 10    # mm left edge -> hole column 1
hole_x2 = 70    # mm left edge -> hole column 2 (= L - 10, symmetric)
hole_y1 = 10    # mm front edge -> hole row 1
hole_y2 = 50    # mm front edge -> hole row 2 (= W - 10, symmetric)
cham = 1        # mm "C1" chamfer on the four vertical outer corners

# ---- derived ----
top_t = H - cavity_h          # mm top plate thickness (= 2)
inner_L = L - 2 * wall        # mm cavity length (= 76)
inner_W = W - 2 * wall        # mm cavity width  (= 56)

with BuildPart() as bp:
    # outer solid, min corner at origin
    Box(L, W, H, align=(Align.MIN, Align.MIN, Align.MIN))

    # C1 chamfer on the four vertical outer corner edges (plan-view callout)
    chamfer(bp.edges().filter_by(Axis.Z), length=cham)

    # hollow interior, open at the bottom (z = 0); leaves 2 mm walls and 2 mm top
    with Locations((wall, wall, 0)):
        Box(inner_L, inner_W, cavity_h,
            align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.SUBTRACT)

    # 4x Ø4 THRU through the top plate (columns x=10,70 ; rows y=10,50)
    pts = [(hole_x1, hole_y1), (hole_x2, hole_y1),
           (hole_x1, hole_y2), (hole_x2, hole_y2)]
    with Locations([(x, y, -1) for (x, y) in pts]):
        Cylinder(radius=hole_d / 2, height=H + 2,
                 align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
