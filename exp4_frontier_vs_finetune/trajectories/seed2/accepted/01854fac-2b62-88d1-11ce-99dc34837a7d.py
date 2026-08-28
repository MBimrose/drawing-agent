# 01854fac-2b62-88d1-11ce-99dc34837a7d — agentic final (cand 1), IoU 0.926
from build123d import *

# ---- named dimensions read from the drawing (mm) ----
plate_x = 80        # mm  overall width  (X): top view = front view
plate_y = 100       # mm  overall depth  (Y): right view overall
plate_t = 5         # mm  thickness      (Z): front/right bars

c1 = 1              # mm  C1 = 45 deg chamfer on the four outer corners

slot_w = 30         # mm  central opening width (X): 25 + 30 + 25 = 80 (centred)
slot_h = 38         # mm  central opening length (Y): right-view 38; 31 + 38 + 31 = 100 (centred)

hole_d = 4          # mm  "6x D4 THRU (2x3)"
hole_col_pitch = 48 # mm  "1x 48" between the 2 columns; edge margin = (80-48)/2 = 16
hole_row_pitch = 12 # mm  "2x 12" between the 3 rows;   end margin = (100-2*12)/2 = 38

# ---- derived centred coordinates ----
# columns: X = 16 and 64 from the left edge  ->  +/-24 about centre
xs = (-hole_col_pitch / 2, hole_col_pitch / 2)
# rows: Y = 38, 50, 62 from the bottom edge  ->  -12, 0, +12 about centre
ys = (-hole_row_pitch, 0.0, hole_row_pitch)

over = 4            # mm  extra length so every cutter passes fully through the 5 mm plate

with BuildPart() as bp:
    # base plate, centred on the origin (Z from -2.5 to +2.5)
    Box(plate_x, plate_y, plate_t)

    # C1 on the four outer corners: at this stage the only Z-parallel edges
    # are the four outer corner edges, so they are the ones chamfered.
    chamfer(edges().filter_by(Axis.Z), length=c1)

    # central through opening (30 x 38), centred
    Box(slot_w, slot_h, plate_t + over, mode=Mode.SUBTRACT)

    # six through holes D4, 2 columns x 3 rows
    with Locations(*[(x, y, 0) for x in xs for y in ys]):
        Cylinder(hole_d / 2, plate_t + over, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
