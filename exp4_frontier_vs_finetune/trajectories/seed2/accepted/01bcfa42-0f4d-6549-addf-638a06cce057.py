# 01bcfa42-0f4d-6549-addf-638a06cce057 — agentic final (cand 1), IoU 1.000
from build123d import *

# --- Dimensions read from the drawing ---
plate_w = 80      # mm, overall X width (front/top views)
plate_d = 60      # mm, overall Y depth (right view)
plate_t = 5       # mm, overall Z thickness (front view)
hole_x = 40       # mm, hole center from left edge (top view)
hole_y = 30       # mm, hole center from front edge (right view)
hole_dia = 6      # mm, blind hole diameter (callout)
hole_depth = 2    # mm, blind hole depth (callout)

with BuildPart() as bp:
    # Base plate, bottom face on Z=0
    Box(plate_w, plate_d, plate_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Blind hole from the top face at (hole_x, hole_y)
    with Locations((hole_x - plate_w / 2, hole_y - plate_d / 2, plate_t)):
        Cylinder(radius=hole_dia / 2, height=hole_depth,
                 align=(Align.CENTER, Align.CENTER, Align.MAX),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
