# 042c25e6-40b8-cd02-4c97-d42363f18b45 — agentic final (cand 1), IoU 0.913
from build123d import *

# ---- dimensions read from the drawing ----
L = 60.0        # mm  overall width  (X), front & top views
W = 40.0        # mm  overall depth  (Y), right side view
H = 20.0        # mm  overall height (Z), front & right side views

hole_d = 6.0    # mm  4x dia6 THRU
x1 = 15.0       # mm  left edge -> 1st hole column (top view, baseline)
x2 = 45.0       # mm  left edge -> 2nd hole column (top view, baseline)
y1 = 10.0       # mm  front edge -> 1st hole row (right view, baseline)
y2 = 30.0       # mm  front edge -> 2nd hole row (right view, baseline)

fillet_r = 2.0  # mm  4x R2 on the corners of every view -> all 12 outer edges

# ---- derived: hole centres relative to the part centre (X,Y centred on origin) ----
xc = (x1 - L / 2, x2 - L / 2)   # (-15, +15)
yc = (y1 - W / 2, y2 - W / 2)   # (-10, +10)
hole_xy = [(x, y) for x in xc for y in yc]

with BuildPart() as bp:
    # plate, X/Y centred, bottom face on z=0
    Box(L, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # R2 on all twelve outer edges (satisfies the "4x R2" note in all three views)
    fillet(bp.edges(), radius=fillet_r)
    # 4 through holes (cut after filleting so the hole rims stay sharp)
    with Locations(*[(x, y, H / 2) for (x, y) in hole_xy]):
        Cylinder(radius=hole_d / 2, height=H + 4,
                 align=(Align.CENTER, Align.CENTER, Align.CENTER),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
