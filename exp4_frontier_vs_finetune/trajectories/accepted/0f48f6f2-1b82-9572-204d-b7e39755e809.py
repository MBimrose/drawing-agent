# 0f48f6f2-1b82-9572-204d-b7e39755e809 — agentic final (cand 1), IoU 0.830
from build123d import *

# ---- dimensions read from the drawing ----
L = 80        # mm  overall length (X), top & front views
W = 50        # mm  overall depth  (Y), right view
H = 30        # mm  overall height (Z), right view
base_h = 13   # mm  solid base height: bottom -> hidden cavity floor (front view)
wall = 3      # mm  wall thickness (the three "3" callouts)
cham = 2      # mm  C2 = 45 deg chamfer, 2 mm (top outer rim edges)

# derived
pocket_d = H - base_h          # mm  pocket depth from top = 30 - 13 = 17
pocket_L = L - 2 * wall        # mm  pocket length = 74
pocket_W = W - 2 * wall        # mm  pocket width  = 44

with BuildPart() as bp:
    # outer solid block, min corner at origin
    Box(L, W, H, align=(Align.MIN, Align.MIN, Align.MIN))

    # C2 chamfer on the four top outer perimeter edges (Z == H) only,
    # done before pocketing so the 3 mm rim is not consumed (chamfer reach 2 < wall 3)
    top_edges = [e for e in bp.edges() if abs(e.center().Z - H) < 1e-6]
    chamfer(top_edges, length=cham)

    # cut the top pocket: inset `wall` on all sides, floor at Z = base_h
    with Locations((wall, wall, base_h)):
        Box(pocket_L, pocket_W, pocket_d,
            align=(Align.MIN, Align.MIN, Align.MIN),
            mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
