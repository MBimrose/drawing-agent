# 03b5b65e-5bdd-f566-8c3c-8743018784cb — agentic final (cand 1), IoU 0.950
from build123d import *

# ---- dimensions read from the drawing (mm) ----
hole_margin_x = 20      # mm  left edge -> 1st hole column (top view)
hole_pitch_x  = 20      # mm  "3x 20" -> 3 pitches = 4 columns
n_col         = 4       #     4 columns in X
hole_margin_y = 15      # mm  edge -> 1st hole row (right view)
hole_pitch_y  = 20      # mm  "2x 20" -> 2 pitches = 3 rows
n_row         = 3       #     3 rows in Y
total_h       = 11      # mm  overall height (front view)
raise_h       = 3       # mm  raised-feature height above base (front view)
pad_dia       = 40      # mm  central raised boss (top view)
hole_dia      = 6       # mm  "12x D6 THRU (3x4)"
rib_w         = 10      # mm  rib width in X (from views; ~2 mm ligament around D6)
rib_len       = 50      # mm  rib length in Y (from views; contains the 3 rows)

# ---- derived ----
W = 2*hole_margin_x + (n_col-1)*hole_pitch_x   # mm  = 20+60+20 = 100 (X overall)
D = 2*hole_margin_y + (n_row-1)*hole_pitch_y   # mm  = 15+40+15 = 70  (Y overall)
base_thk = total_h - raise_h                   # mm  = 11-3 = 8

col_xs = [-W/2 + hole_margin_x + i*hole_pitch_x for i in range(n_col)]  # -30,-10,10,30
row_ys = [-D/2 + hole_margin_y + j*hole_pitch_y for j in range(n_row)]  # -20,0,20
rib_xs = [col_xs[0], col_xs[-1]]                                        # outer columns ±30
hole_pts = [(x, y, 0) for x in col_xs for y in row_ys]                  # 12 holes

with BuildPart() as bp:
    # base plate (Z: 0 .. base_thk)
    Box(W, D, base_thk, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # central raised boss (Z: base_thk .. total_h)
    with Locations((0, 0, base_thk)):
        Cylinder(radius=pad_dia/2, height=raise_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # two raised ribs on the outer hole columns
    with Locations(*[(x, 0, base_thk) for x in rib_xs]):
        Box(rib_w, rib_len, raise_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # 12 through-holes
    with Locations(*hole_pts):
        Cylinder(radius=hole_dia/2, height=total_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
