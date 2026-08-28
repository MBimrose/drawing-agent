# 02b4260a-2c89-b076-eed5-bd1a05cc4df7 — agentic final (cand 1), IoU 1.000
from build123d import *

# --- Dimensions read from the drawing ---
plate_len = 80        # mm  overall length (X), top view
plate_wid = 60        # mm  overall width (Y), right side view
plate_thk = 7         # mm  plate thickness (Z), front view
edge_chamfer = 0.5    # mm  C0.5 chamfer on the four vertical corner edges

hole_dia = 5          # mm  8x Ø5 THRU (2 rows x 4 columns)
hole_edge_dist = 10   # mm  first hole column from the left edge
hole_pitch = 20       # mm  column spacing (3x 20)
row_spacing = 30      # mm  spacing between the two rows (1x 30), symmetric about centre

recess_dia = 30       # mm  Ø30 central recess
recess_depth = 2      # mm  recess depth (↓2) from the top face
# recess centred: dimensioned 40 from left edge = half of the 80 length

# --- Derived values ---
x0 = -plate_len / 2 + hole_edge_dist                 # first column X = -30
col_xs = [x0 + i * hole_pitch for i in range(4)]     # -30, -10, +10, +30
row_ys = [-row_spacing / 2, row_spacing / 2]         # -15, +15

with BuildPart() as builder:
    # base plate, bottom face on Z = 0
    Box(plate_len, plate_wid, plate_thk,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # central Ø30 x 2 deep recess in the top face
    with Locations((0, 0, plate_thk - recess_depth)):
        Cylinder(radius=recess_dia / 2, height=recess_depth,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    # 8x Ø5 through holes
    hole_pts = [(x, y) for x in col_xs for y in row_ys]
    with Locations(hole_pts):
        Cylinder(radius=hole_dia / 2, height=plate_thk,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    # C0.5 chamfers on the four vertical corner edges
    chamfer(builder.edges().filter_by(Axis.Z), length=edge_chamfer)

part = builder.part
export_step(part, "output.step")
