# 0d8231a8-81fd-47f7-9899-42026b48074c — agentic final (cand 1), IoU 1.000
from build123d import *

# --- Dimensions read from drawing ---
width_x = 50   # mm - overall width (X), top & front views
depth_y = 80   # mm - overall depth (Y), right view
height_z = 30  # mm - overall height (Z), front view
cham = 1       # mm - C1: 45 deg chamfer, 1 mm leg, called out on all corners (all 12 edges)

with BuildPart() as bp:
    Box(width_x, depth_y, height_z)
    chamfer(bp.edges(), length=cham)

part = bp.part
export_step(part, "output.step")
