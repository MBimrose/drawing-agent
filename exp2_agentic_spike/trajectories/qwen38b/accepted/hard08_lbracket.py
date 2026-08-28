# hard08_lbracket — agentic final (cand 3), IoU 0.966
from build123d import *

# ---- dimensions read from the drawing ----
t_vert  = 12.0           # mm  vertical plate thickness (Top view left strip)
seg     = 68.0           # mm  Top/Front view: vertical-plate face to right edge
W       = t_vert + seg   # mm  overall X = 12 + 68 = 80
D       = 45.0           # mm  overall depth Y (Top view, confirmed by Right view width)
h_above = 51.0           # mm  vertical plate height ABOVE the base top (Front & Right views)
t_base  = 12.0           # mm  base plate thickness (Right view bottom strip)
H       = h_above + t_base  # mm  overall Z = 51 + 12 = 63
d_boss  = 7.0            # mm  boss diameter (Top view circle callout)
boss_h  = 12.0           # mm  boss height (not dimensioned -> matched to drawing proportion)
boss_x  = W - 19.0       # mm  boss center, ~19 mm from right edge (undimensioned, from Top view)
boss_y  = D / 2.0        # mm  boss centered in depth (symmetry, Right view)

with BuildPart() as ctx:
    # horizontal base plate
    Box(W, D, t_base, align=(Align.MIN, Align.MIN, Align.MIN))
    # vertical plate at the left end, full depth, full overall height
    Box(t_vert, D, H, align=(Align.MIN, Align.MIN, Align.MIN))
    # cylindrical hub boss on the base plate (positioned via Locations)
    with Locations((boss_x, boss_y, t_base)):
        Cylinder(d_boss / 2.0, boss_h, align=(Align.CENTER, Align.CENTER, Align.MIN))

part = ctx.part
export_step(part, "output.step")
