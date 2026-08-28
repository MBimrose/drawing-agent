# std07_lbracket — agentic final (cand 2), IoU 0.981
# one complete runnable script
from build123d import *

# ---- dimensions read from the drawing ----
L = 83          # mm, overall length (Top view)
D = 40          # mm, overall depth (Top view)
H = 60          # mm, overall height (Right view)
base_len = 72   # mm, base plate length from wall face (Top view)
h_to_plate = 49 # mm, wall top to plate top (Right view)
boss_d = 8      # mm, boss diameter (Top view callout)
boss_h = 8      # mm, boss height above plate (Right view)
boss_x = 63     # mm, boss center from left end (read in Top view, 20 from right)

# ---- derived values ----
wall_t = L - base_len        # 11 mm, wall thickness
plate_t = H - h_to_plate     # 11 mm, base plate thickness
boss_y = D / 2               # 20 mm, boss centered in depth

with BuildPart() as m:
    # base plate
    Box(L, D, plate_t, align=(Align.MIN, Align.MIN, Align.MIN))
    # vertical wall at left end
    Box(wall_t, D, H, align=(Align.MIN, Align.MIN, Align.MIN))
    # cylindrical boss on plate top
    with Locations((boss_x, boss_y, plate_t)):
        Cylinder(boss_d / 2, boss_h, align=(Align.CENTER, Align.CENTER, Align.MIN))

part = m.part

export_step(part, "output.step")
