# 0cfca2a4-82f2-1b33-7d3e-2b686d1df698 — agentic final (cand 1), IoU 0.980
from build123d import *
import math

# ---- dimensions read from the drawing ----
L = 80.0            # mm  overall length (X), top & front views
W = 25.0            # mm  overall width (Y), right side view
T = 5.0             # mm  overall thickness (Z), front & right views
R_SCOOP = 15.0      # mm  radius of the concave end arc (passes through both
                    #     left corners, chord = full 25 mm width)
CHAM = 0.5          # mm  C0.5 chamfer on the right end face edges (4 callouts)

# derived: scoop arc centre lies on the part centreline, outside the left edge,
# at distance sqrt(R^2 - (W/2)^2) from the left-edge chord
scoop_cx = -math.sqrt(R_SCOOP**2 - (W / 2) ** 2)   # mm, ~ -8.29

with BuildPart() as bp:
    # base plate: X = length, Y = width, Z = thickness, corner at origin
    Box(L, W, T, align=(Align.MIN, Align.MIN, Align.MIN))

    # concave cylindrical scoop through the full thickness at the -X end
    with Locations((scoop_cx, W / 2, T / 2)):
        Cylinder(radius=R_SCOOP, height=T + 2, mode=Mode.SUBTRACT)

    # C0.5 chamfers on the four edges of the right (+X) end face
    end_edges = [e for e in bp.edges() if abs(e.center().X - L) < 1e-6]
    chamfer(end_edges, CHAM)

part = bp.part
export_step(part, "output.step")
