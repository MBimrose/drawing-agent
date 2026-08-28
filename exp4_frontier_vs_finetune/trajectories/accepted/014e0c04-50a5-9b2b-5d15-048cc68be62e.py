# 014e0c04-50a5-9b2b-5d15-048cc68be62e — agentic final (cand 1), IoU 0.875
from build123d import *

# ---- dimensions read from the drawing (mm) ----
plate_L = 80.0                 # mm  overall X (FRONT view)
plate_W = 35.0                 # mm  base plate width in Y (RIGHT view, lower block)
plate_T = 6.0                  # mm  base plate thickness (FRONT view)
total_H = 9.0                  # mm  overall height (FRONT view)
rib_H   = total_H - plate_T    # mm  rib height above plate = 3
rib_x1  = 37.0                 # mm  rib left edge from left end (TOP)
rib_x2  = 43.0                 # mm  rib right edge from left end (TOP)
rib_W   = rib_x2 - rib_x1      # mm  rib width in X = 6 (centred at 40 = plate_L/2)
rib_L   = 70.0                 # mm  rib length in Y (RIGHT view upper cap; overhangs plate)
hole_d  = 5.0                  # mm  2x Ø5 THRU
hole_x_left  = 15.0            # mm  left hole centre from left edge (TOP)
hole_x_right = 65.0            # mm  right hole centre from left edge (= plate_L - 15, symmetric)
c_cham  = 0.5                  # mm  C0.5 on the four outer plan corners of the base

with BuildPart() as bp:
    # base plate: X 0..80, Y centred on 0, Z 0..6
    with Locations((plate_L / 2, 0, plate_T / 2)):
        Box(plate_L, plate_W, plate_T)

    # rib on top of the plate: X 37..43 (centre 40), Y -35..35, Z 6..9
    with Locations(((rib_x1 + rib_x2) / 2, 0, plate_T + rib_H / 2)):
        Box(rib_W, rib_L, rib_H)

    # two through holes in the base plate (Y centred = mid of plate_W)
    with Locations((hole_x_left, 0, -1), (hole_x_right, 0, -1)):
        Cylinder(hole_d / 2, plate_T + 2,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    # C0.5 chamfer on the four outer vertical corner edges of the base plate
    corner_edges = [e for e in bp.edges().filter_by(Axis.Z)
                    if abs(e.length - plate_T) < 1e-3]
    chamfer(corner_edges, c_cham)

part = bp.part
export_step(part, "output.step")
