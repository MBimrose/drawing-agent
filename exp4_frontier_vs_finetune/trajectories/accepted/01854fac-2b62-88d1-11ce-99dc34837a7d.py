# 01854fac-2b62-88d1-11ce-99dc34837a7d — agentic final (cand 1), IoU 0.923
from build123d import *

# ---------- dimensions read from the drawing ----------
plate_w = 80          # mm - plate width X (top & front views)
plate_d = 100         # mm - plate depth Y (top & right views)
plate_t = 5           # mm - plate thickness Z (front & right views)
c_corner = 1          # mm - "C1" chamfer on all four vertical corners

slot_w = 30           # mm - central rounded-rectangle slot width (X)
slot_d = 38           # mm - central rounded-rectangle slot depth (Y, from right view)
slot_r = 5            # mm - slot corner radius (not dimensioned, estimated)

hole_d = 4            # mm - "6x ⌀4 THRU (2x3)"
hole_col_edge = 16    # mm - left hole column centre from left plate edge
hole_col_pitch = 48   # mm - hole column spacing ("1x 48")
hole_row_edge = 39    # mm - first hole row centre from back plate edge
hole_row_pitch = 12   # mm - hole row spacing ("2x 12")

# ---------- derived positions (plate centred on the origin) ----------
col_xs = (-plate_w / 2 + hole_col_edge,
          -plate_w / 2 + hole_col_edge + hole_col_pitch)            # -24, +24
row_ys = tuple(plate_d / 2 - hole_row_edge - i * hole_row_pitch
               for i in range(3))                                    # +11, -1, -13
hole_pts = [(x, y) for x in col_xs for y in row_ys]

with BuildPart() as bp:
    # base plate
    with BuildSketch():
        Rectangle(plate_w, plate_d)
    extrude(amount=plate_t)

    # C1 chamfers on the four vertical corner edges
    chamfer(bp.edges().filter_by(Axis.Z), length=c_corner)

    # central rounded-rectangle through slot
    with BuildSketch():
        RectangleRounded(slot_w, slot_d, slot_r)
    extrude(amount=plate_t, mode=Mode.SUBTRACT)

    # six through holes (2 columns x 3 rows)
    with BuildSketch():
        with Locations(hole_pts):
            Circle(hole_d / 2)
    extrude(amount=plate_t, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
