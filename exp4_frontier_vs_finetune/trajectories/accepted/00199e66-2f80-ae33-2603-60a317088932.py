# 00199e66-2f80-ae33-2603-60a317088932 — agentic final (cand 1), IoU 0.976
from build123d import *
from math import tan, radians

# ---------------- dimensions read from the drawing ----------------
plate_L = 80            # mm  overall width (X), top view bottom dimension
plate_W = 60            # mm  overall depth (Y), right view chain: 15 + 30 + 15 = 60
plate_T = 12            # mm  plate thickness (Z), front/right views

col_1_x = 15            # mm  first hole column from left edge
col_pitch = 40          # mm  column-to-column spacing (col 2 at 55; check dim 80-15=65)
row_1_y = 15            # mm  first hole row from front edge
row_pitch = 30          # mm  row-to-row spacing (row 2 at 45 = 15+30)

thru_d = 5              # mm  callout: 4x Ø5 THRU
csk_d = 10              # mm  callout: countersink Ø10
csk_angle = 82          # deg callout: countersink included angle 82°

blind_d = 30            # mm  callout: Ø30 central hole
blind_depth = 6         # mm  callout: depth ↓6 (blind, from top face)

c1 = 1                  # mm  C1 chamfer, four vertical corner edges

# ---------------- derived values ----------------
hole_xy = [(x - plate_L / 2, y - plate_W / 2)
           for x in (col_1_x, col_1_x + col_pitch)      # -25, +15 about center
           for y in (row_1_y, row_1_y + row_pitch)]     # -15, +15 about center
csk_half = radians(csk_angle / 2)
csk_depth = (csk_d - thru_d) / 2 / tan(csk_half)        # ≈ 2.88 mm
overcut = 1                                             # mm extra so boolean cuts exit cleanly
csk_top_r = csk_d / 2 + overcut / tan(csk_half)         # cone radius extended above top face

with BuildPart() as builder:
    # base plate
    with BuildSketch():
        Rectangle(plate_L, plate_W)
    extrude(amount=plate_T)

    # 4x Ø5 through drills
    with Locations([(x, y, plate_T / 2) for x, y in hole_xy]):
        Cylinder(radius=thru_d / 2, height=plate_T + 2 * overcut,
                 mode=Mode.SUBTRACT)

    # 4x Ø10 x 82° countersinks from the top face
    with Locations([(x, y, plate_T - csk_depth) for x, y in hole_xy]):
        Cone(bottom_radius=thru_d / 2, top_radius=csk_top_r,
             height=csk_depth + overcut,
             align=(Align.CENTER, Align.CENTER, Align.MIN),
             mode=Mode.SUBTRACT)

    # central Ø30 blind hole, 6 mm deep from the top face
    with Locations((0, 0, plate_T - blind_depth)):
        Cylinder(radius=blind_d / 2, height=blind_depth + overcut,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    # C1 chamfers on the four vertical corner edges
    chamfer(builder.edges().filter_by(Axis.Z), length=c1)

part = builder.part
export_step(part, "output.step")
