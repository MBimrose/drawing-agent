# 0a8774b8-ccb0-2954-6720-39bba429eb91 — agentic final (cand 2), IoU 0.999
from build123d import *

# ---------- Dimensions read from the drawing ----------
plate_L = 80        # mm  overall length (X) - top & front views
plate_W = 60        # mm  overall width  (Y) - top & right views
plate_T = 8         # mm  thickness (Z) - front & right views
corner_chamfer = 2  # mm  C2 chamfer on the four vertical corner edges

# 4x dia5 THRU corner holes, 10 mm from each edge
h5_dia = 5          # mm
h5_off = 10         # mm  edge offset (dims 10, 70=80-10, 50=60-10)

# 6x dia4 THRU holes in a 2x3 array
h4_dia = 4          # mm
h4_x0 = 50          # mm  first column from left edge (dim 50)
h4_dx = 12          # mm  column pitch (dim 2x12) -> x = 50, 62, 74
h4_y0 = 40          # mm  first row from front edge (dim 40)
h4_dy = 12          # mm  row pitch (dim 1x12) -> y = 40, 52

# ---------- Derived hole positions (part centered on origin) ----------
pts5 = [(x, y)
        for x in (-plate_L/2 + h5_off, plate_L/2 - h5_off)
        for y in (-plate_W/2 + h5_off, plate_W/2 - h5_off)]

pts4 = [(h4_x0 + i * h4_dx - plate_L/2,
         h4_y0 + j * h4_dy - plate_W/2)
        for i in range(3) for j in range(2)]

# ---------- Build ----------
with BuildPart() as bp:
    with BuildSketch():
        Rectangle(plate_L, plate_W)
        with Locations(pts5):
            Circle(h5_dia / 2, mode=Mode.SUBTRACT)   # 4x dia5 THRU
        with Locations(pts4):
            Circle(h4_dia / 2, mode=Mode.SUBTRACT)   # 6x dia4 THRU (2x3)
    extrude(amount=plate_T)
    # C2 chamfer on the four vertical corner edges
    chamfer(bp.edges().filter_by(Axis.Z), length=corner_chamfer)

part = bp.part
export_step(part, "output.step")
