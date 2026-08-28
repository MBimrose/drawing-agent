# 0ead60ac-739e-453e-0ca0-c687a546b676 — agentic final (cand 1), IoU 1.000
from build123d import *

# ---- dimensions read from the drawing ----
L = 80.0        # mm  overall length (X) - front view overall dimension
W = 20.0        # mm  overall width  (Y) - right view
H = 10.0        # mm  overall height (Z) - right view
HOLE_D = 4.0    # mm  "2x Ø4 THRU" - vertical through-holes
HOLE_X1 = 25.0  # mm  hole 1 centre from the -X end (top view)
HOLE_X2 = 55.0  # mm  hole 2 centre from the -X end (top view)
HOLE_Y = 10.0   # mm  hole centre across width (right view) = mid-width
CH = 0.5        # mm  C0.5 chamfer on the four longitudinal edges

# derived positions (part centred on origin)
x1 = HOLE_X1 - L / 2   # -15 mm
x2 = HOLE_X2 - L / 2   # +15 mm
yc = HOLE_Y - W / 2    #   0 mm

with BuildPart() as bp:
    Box(L, W, H)
    # 2x Ø4 through-holes (vertical, through the 10 mm thickness)
    with Locations((x1, yc, 0), (x2, yc, 0)):
        Cylinder(radius=HOLE_D / 2, height=H + 2,
                 align=(Align.CENTER, Align.CENTER, Align.CENTER),
                 mode=Mode.SUBTRACT)
    # C0.5 chamfers on the four edges parallel to X
    chamfer(bp.edges().filter_by(Axis.X), length=CH)

part = bp.part
export_step(part, "output.step")
