# std07_lbracket — agentic final (cand 3), IoU 0.975
from build123d import *

# ---- Dimensions read from the drawing (mm) ----
overall_x  = 83.0   # mm  Top view overall width (X)
depth_y    = 40.0   # mm  Top view depth (Y)
overall_z  = 60.0   # mm  Right view overall height (Z)
base_len_x = 72.0   # mm  Top view component (base length, wall face -> right edge)
wall_above = 49.0   # mm  Right view component (wall height above base top)

# ---- Derived values ----
wall_thk = overall_x - base_len_x   # 83 - 72 = 11  wall thickness
base_thk = overall_z - wall_above   # 60 - 49 = 11  base plate thickness

# ---- Boss (cylinder on base) ----
boss_dia = 10.0    # mm
boss_h   = 10.0    # mm
boss_x   = 63.0    # mm  from left edge (read from Top view)
boss_y   = depth_y / 2.0   # mm  centered in depth

# ---- Build the solid (place each primitive via a Vector Location) ----
with BuildPart() as bp:
    # Base plate: X 0..83, Y 0..40, Z 0..11
    with Locations([Location(Vector(overall_x / 2.0, depth_y / 2.0, base_thk / 2.0))]):
        Box(overall_x, depth_y, base_thk)
    # Vertical wall at left end: X 0..11, Y 0..40, Z 0..60
    with Locations([Location(Vector(wall_thk / 2.0, depth_y / 2.0, overall_z / 2.0))]):
        Box(wall_thk, depth_y, overall_z)
    # Boss cylinder on top of base
    with Locations([Location(Vector(boss_x, boss_y, base_thk + boss_h / 2.0))]):
        Cylinder(boss_dia / 2.0, boss_h)

part = bp.part

export_step(part, "output.step")
