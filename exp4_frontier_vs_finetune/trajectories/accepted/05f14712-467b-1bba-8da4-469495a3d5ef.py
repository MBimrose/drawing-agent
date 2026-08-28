# 05f14712-467b-1bba-8da4-469495a3d5ef — agentic final (cand 1), IoU 0.890
from build123d import *
from math import tan, radians

# ---------------- dimensions read from the drawing ----------------
L = 70.0        # mm  overall length (X) - top view bottom dim / front view width
W = 50.0        # mm  overall depth  (Y) - right view bottom dim
H = 30.0        # mm  overall height (Z) - front view

# bottom pocket (hidden rectangle in top/front/right views, dashed box in ISO)
pocket_L = 60.0                 # mm  pocket length (X) - top view dim (x = 5..65)
pocket_W = 40.0 - 10.0          # mm  pocket width (Y) - right view chain 10..40 = 30
pocket_D = H - 22.5             # mm  pocket depth from bottom: ceiling is 22.5 below top = 7.5

# 2x D12 THRU (vertical), on the X centerline
d_big = 12.0                    # mm
x_big = 35.0 - 20.0             # mm  centers at X=20 and X=50 -> +/-15 about center

# 4x D4 THRU with D6 x 90 deg countersink on the top face
d_small = 4.0                   # mm
d_csink = 6.0                   # mm
a_csink = 90.0                  # deg
x_small = 35.0 - 10.0           # mm  columns at X=10 and X=60 -> +/-25
y_small = 15.0                  # mm  rows +/-15 about the Y center plane (top view "15")

# D6 THRU cross hole along X (circle in the right view)
d_cross = 6.0                   # mm
z_cross = 22.5                  # mm  center height above bottom (front view)

c1 = 1.0                        # mm  C1 chamfer on the four top perimeter edges
r1 = 1.0                        # mm  R1 fillet on the four vertical corner edges

csink_depth = (d_csink - d_small) / 2 / tan(radians(a_csink / 2))  # = 1 mm

with BuildPart() as bp:
    # base block: centered in X/Y, bottom face on Z=0
    Box(L, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # bottom pocket, centered in X/Y, open at the bottom
    Box(pocket_L, pocket_W, pocket_D,
        align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

    # 2x D12 through holes
    with Locations([(-x_big, 0, 0), (x_big, 0, 0)]):
        Cylinder(radius=d_big / 2, height=H,
                 align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

    # 4x D4 through holes
    pts = [(sx * x_small, sy * y_small) for sx in (-1, 1) for sy in (-1, 1)]
    with Locations([(x, y, 0) for x, y in pts]):
        Cylinder(radius=d_small / 2, height=H,
                 align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    # 90 deg countersinks on the top face (D6 at surface -> D4 at 1 mm depth)
    with Locations([(x, y, H - csink_depth) for x, y in pts]):
        Cone(bottom_radius=d_small / 2, top_radius=d_csink / 2, height=csink_depth,
             align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

    # D6 through hole along X at mid-depth (y=0), z = 22.5
    with Locations((0, 0, z_cross)):
        Cylinder(radius=d_cross / 2, height=L + 4, rotation=(0, 90, 0),
                 mode=Mode.SUBTRACT)

    # C1 chamfer on the four top perimeter edges
    top_edges = [e for e in bp.edges()
                 if e.geom_type == GeomType.LINE
                 and abs(e.center().Z - H) < 1e-4
                 and (abs(abs(e.center().X) - L / 2) < 1e-4
                      or abs(abs(e.center().Y) - W / 2) < 1e-4)]
    chamfer(top_edges, length=c1)

    # R1 fillet on the four vertical corner edges
    corner_edges = [e for e in bp.edges()
                    if e.geom_type == GeomType.LINE
                    and abs(abs(e.center().X) - L / 2) < 1e-4
                    and abs(abs(e.center().Y) - W / 2) < 1e-4
                    and e.bounding_box().size.Z > H / 2]
    fillet(corner_edges, radius=r1)

part = bp.part
export_step(part, "output.step")
