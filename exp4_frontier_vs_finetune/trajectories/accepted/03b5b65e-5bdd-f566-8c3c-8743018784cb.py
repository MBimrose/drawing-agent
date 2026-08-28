# 03b5b65e-5bdd-f566-8c3c-8743018784cb — agentic final (cand 3), IoU 0.941
from build123d import *

# ---------- dimensions read from the drawing ----------
col_margin = 20      # mm  plate X edge -> first hole column
col_pitch  = 20      # mm  "3x 20" hole column spacing
row_margin = 15      # mm  plate Y edge -> first hole row (right view)
row_pitch  = 20      # mm  "2x 20" hole row spacing
plate_Y    = 70      # mm  overall depth (right view)
total_H    = 11      # mm  overall height (front view)
pad_H      = 3       # mm  raised feature height (front view)
hole_D     = 6       # mm  12x ⌀6 THRU (3x4)
boss_D     = 40      # mm  central round boss ⌀40
rail_W     = 10      # mm  rail width (undimensioned; = pitch/2 from view proportions)
rail_end   = 10      # mm  rail extension beyond outer hole rows (right view: ~5 mm margins to plate edges)

# ---------- derived values ----------
plate_X = 2 * col_margin + 3 * col_pitch        # 20 + 3*20 + 20 = 100 mm
base_H  = total_H - pad_H                       # 8 mm base plate thickness
rail_L  = 2 * row_pitch + 2 * rail_end          # 40 + 2*10 = 60 mm (Y = 5..65)
cols = [col_margin + i * col_pitch for i in range(4)]   # X = 20, 40, 60, 80
rows = [row_margin + i * row_pitch for i in range(3)]   # Y = 15, 35, 55
cx, cy = plate_X / 2, plate_Y / 2               # part centre (50, 35)

with BuildPart() as bp:
    # base plate
    Box(plate_X, plate_Y, base_H, align=(Align.MIN, Align.MIN, Align.MIN))
    # central ⌀40 boss, 3 mm high
    with Locations((cx, cy, base_H)):
        Cylinder(boss_D / 2, pad_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # two side rails on the outer hole columns
    with Locations((cols[0], cy, base_H), (cols[-1], cy, base_H)):
        Box(rail_W, rail_L, pad_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # 12 through holes ⌀6 (4 x 3 grid)
    hole_pts = [(x, y) for x in cols for y in rows]
    with Locations(hole_pts):
        Cylinder(hole_D / 2, total_H,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
