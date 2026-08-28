# 0cb7362e-5998-2862-8a9a-6aa7e782436c — agentic final (cand 2), IoU 1.000
from build123d import *

# ---------------- dimensions from the drawing ----------------
L = 80           # mm  overall length (X)
W = 30           # mm  overall width  (Y)
T = 10           # mm  overall height (Z)

hole_dia = 4     # mm  through hole: ⌀4 THRU
cbore_dia = 7    # mm  counterbore diameter: ⌴ ⌀7
cbore_depth = 2  # mm  counterbore depth: ↓2 (from the bottom face)

hole_x = 76      # mm  hole centre from the left end (4 mm from the right end)
hole_y = 15      # mm  hole centre from the front edge (centred in the 30 width)

cham = 1         # mm  C1 chamfer on the four vertical corner edges

# derived positions relative to the part centre
hx = hole_x - L / 2   # = +36 mm
hy = hole_y - W / 2   # = 0 (centred)

with BuildPart() as bp:
    # base bar
    with BuildSketch(Plane.XY):
        Rectangle(L, W)
    extrude(amount=T)

    # ⌀4 through hole (oversized in Z for a clean cut)
    with Locations((hx, hy, T / 2)):
        Cylinder(hole_dia / 2, T + 2, mode=Mode.SUBTRACT)

    # ⌀7 × 2 counterbore from the bottom face
    with Locations((hx, hy, cbore_depth / 2)):
        Cylinder(cbore_dia / 2, cbore_depth, mode=Mode.SUBTRACT)

    # C1 chamfers on the four vertical corner edges
    chamfer(bp.edges().filter_by(Axis.Z), length=cham)

# bind the finished solid (not the BuildPart context) to `part`
part = bp.part

export_step(part, "output.step")
