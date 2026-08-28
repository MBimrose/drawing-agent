# 0a01a8f6-a78b-1b51-8435-ede6e4562a4d — agentic final (cand 1), IoU 0.998
from build123d import *

# ---------------- Dimensions from the drawing ----------------
len_x = 80      # mm - overall length of long leg (X), top view
len_y = 30      # mm - overall length of short leg (Y), right view
leg_w = 5       # mm - plan width of the bar legs (front & right views)
hgt_z = 10      # mm - height of the bar (Z), front & right views
r2 = 2          # mm - fillet radius: "5x R2" (plan convex corners) and
                #      "6x R2" (top/bottom rims per front/right views)

TOL = 1e-3

with BuildPart() as bp:
    # L footprint: long leg along X, short leg along Y at the X=0 end
    Box(len_x, leg_w, hgt_z, align=(Align.MIN, Align.MIN, Align.MIN))  # long leg
    Box(leg_w, len_y, hgt_z, align=(Align.MIN, Align.MIN, Align.MIN))  # short leg

    # 5x R2 - fillet the five convex vertical edges;
    # the re-entrant inner corner at (leg_w, leg_w) stays sharp
    convex_vertical_edges = [
        e for e in bp.edges().filter_by(Axis.Z)
        if not (abs(e.center().X - leg_w) < TOL and abs(e.center().Y - leg_w) < TOL)
    ]
    fillet(convex_vertical_edges, radius=r2)

    # 6x R2 - fillet the complete top and bottom rim edges
    # (appears as 6 rounded corners in each of the front and right views)
    rim_edges = [
        e for e in bp.edges()
        if abs(e.center().Z) < TOL or abs(e.center().Z - hgt_z) < TOL
    ]
    fillet(rim_edges, radius=r2)

part = bp.part
export_step(part, "output.step")
