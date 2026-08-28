# 0979b252-eee8-3278-1a58-0188807a4b43 — agentic final (cand 1), IoU 0.974
from build123d import *

# ============ dimensions read from the drawing ============
L = 80.0                 # mm  overall length (X) - top/front views
W = 30.0                 # mm  overall depth (Y) - right view
T = 8.0                  # mm  overall thickness (Z) - front/right views

hole_dia = 5.0           # mm  "2x ⌀5 THRU"
hole_x1 = 20.0           # mm  left hole centre from left edge (top view)
hole_x2 = 60.0           # mm  right hole centre from left edge (top view)
feature_y = 15.0         # mm  hole/hex centre plane from front edge (right view)

hex_across_corners = 10.0  # mm  hex through-hole across corners
                           #     (no callout; scaled from the 1:1 views, 5 mm side)

ch = 0.5                 # mm  "C0.5" chamfer at the four top corners

# ---- derived positions (part centred on the origin) ----
x1 = hole_x1 - L / 2     # left hole X  = -20
x2 = hole_x2 - L / 2     # right hole X = +20
yc = feature_y - W / 2   # feature Y    = 0

with BuildPart() as bp:
    # base plate, bottom face on the XY plane
    with BuildSketch(Plane.XY):
        Rectangle(L, W)
    extrude(amount=T)

    # C0.5 chamfer around the top perimeter (done before the cuts so the
    # top group contains only the four outer edges)
    chamfer(bp.edges().group_by(Axis.Z)[-1], length=ch)

    # through features: two round holes + central hexagon (vertex on +X,
    # i.e. flats top/bottom as drawn)
    with BuildSketch(Plane.XY):
        with Locations((x1, yc), (x2, yc)):
            Circle(hole_dia / 2)
        RegularPolygon(hex_across_corners / 2, 6)
    extrude(amount=T, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
