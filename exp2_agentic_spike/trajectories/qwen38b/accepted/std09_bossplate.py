# std09_bossplate — agentic final (cand 4), IoU 0.850
from build123d import *

# ---- dimensions read from the drawing (mm) ----
overall_h = 31.0   # mm, Right view overall height
boss_h    = 20.0   # mm, Right view boss height
plate_t   = overall_h - boss_h   # 11 mm, plate thickness (31 - 20)
plate_y   = 50.0   # mm, Top view overall width (Y)
plate_x   = 100.0  # mm, Top view overall length (X), from view proportion
boss_y    = 20.0   # mm, Top view boss width (Y)
boss_x    = 40.0   # mm, Top view boss length (X), from view proportion
hole_d    = 12.0   # mm, "O12 THRU"

# ---- build ----
with BuildPart() as bp:
    # base plate, centered in X/Y, bottom face at z=0
    Box(plate_x, plate_y, plate_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    # boss centered on plate top: translate by plate thickness (Vector form)
    with Locations(Location(Vector(0, 0, plate_t))):
        Box(boss_x, boss_y, boss_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
    # centered through hole (boss + plate)
    Cylinder(hole_d / 2, overall_h,
             align=(Align.CENTER, Align.CENTER, Align.MIN),
             mode=Mode.SUBTRACT)

part = bp.part

export_step(part, "output.step")
