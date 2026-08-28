# 038de502-dae8-4b1f-95d1-74f6139edbf0 — agentic final (cand 1), IoU 1.000
from build123d import *
from math import cos, sin, radians

# ---- named dimensions read from the drawing ----
half = 40                  # mm, centerline -> plate edge (given as 40 on each side)
plate_w = half + half      # mm, overall X = 40 + 40 = 80
plate_d = half + half      # mm, overall Y = 40 + 40 = 80 (square; gives 10 mm margin to Ø60 BC)
thickness = 5              # mm, plate thickness (front / side views)
corner_r = 4               # mm, 4x R4 corner fillets
slot_half_len = 20         # mm, center -> slot end (given as 20)
slot_len = 2 * slot_half_len  # mm, central slot length in X = 40
slot_w = 15                # mm, central slot width in Y
hole_d = 5                 # mm, 8x Ø5 THRU
bolt_circle_d = 60         # mm, Ø60 bolt circle
n_holes = 8                # EQ SP

bc_r = bolt_circle_d / 2   # mm, bolt-circle radius = 30
hole_r = hole_d / 2        # mm

with BuildPart() as bp:
    # base plate, bottom face on Z=0
    Box(plate_w, plate_d, thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # 4x R4 on the outer vertical corners (the plain box has exactly 4 Z-edges)
    fillet(bp.edges().filter_by(Axis.Z), radius=corner_r)

    # central through-slot 40 (X) x 15 (Y)
    Box(slot_len, slot_w, thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
        mode=Mode.SUBTRACT)

    # 8x Ø5 through-holes equally spaced (45 deg) on Ø60 BC, first hole on +X axis
    pts = [(bc_r * cos(radians(i * 360 / n_holes)),
            bc_r * sin(radians(i * 360 / n_holes)),
            -1) for i in range(n_holes)]   # start below the plate to guarantee THRU
    with Locations(*pts):
        Cylinder(hole_r, thickness + 2,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
