# 087bbb7a-c871-f9b6-b640-7e8ce9aa5dbf — agentic final (cand 1), IoU 0.973
from build123d import *

# ---- dimensions read from the drawing ----
L = 100          # mm  overall length (X)
W = 30           # mm  overall width  (Y)
H = 20           # mm  overall height (Z)
t = 2            # mm  outer wall thickness (sides, top, bottom)
web = 6          # mm  central longitudinal web thickness (Y)
hole_d = 4       # mm  hole diameter (4x)
hole_depth = 18  # mm  blind-hole depth from the front (-Y) face
hole_pitch = 15  # mm  hole spacing (3x 15 across 4 holes)
n_holes = 4      #     number of holes
r_in = 1         # mm  internal corner fillet (4x R1)

# ---- derived values ----
cav_w = (W - 2 * t - web) / 2   # mm  width of each channel (Y) = (30-4-6)/2 = 10
cav_h = H - 2 * t               # mm  channel height (Z) = 20-4 = 16
cav_off = web / 2 + cav_w / 2   # mm  channel centre offset from mid-plane (Y) = 3+5 = 8
y_hole = -W / 2 + hole_depth / 2  # mm  hole-cylinder centre in Y = -15+9 = -6 (spans -15..+3)
xs = [(i - (n_holes - 1) / 2) * hole_pitch for i in range(n_holes)]  # -22.5,-7.5,7.5,22.5

with BuildPart() as bp:
    # YZ cross-section extruded along X (centred): outer tube minus two rounded channels
    with BuildSketch(Plane.YZ):
        Rectangle(W, H)  # outer 30 (Y) x 20 (Z)
        for s in (-1, 1):
            with Locations((s * cav_off, 0)):
                RectangleRounded(cav_w, cav_h, r_in, mode=Mode.SUBTRACT)
    extrude(amount=L / 2, both=True)  # X from -50 to +50

    # 4 blind holes from the front (-Y) face, depth 18 (through front wall + web, stop at rear cavity)
    for x in xs:
        with Locations((x, y_hole, 0)):
            Cylinder(radius=hole_d / 2, height=hole_depth,
                     rotation=(90, 0, 0), mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
