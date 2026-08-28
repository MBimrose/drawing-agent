# 01bcfa42-0f4d-6549-addf-638a06cce057 — agentic final (cand 1), IoU 1.000
from build123d import *

# --- Dimensions read from the drawing ---
plate_len = 80      # mm, overall length (X), top & front views
plate_wid = 60      # mm, overall width (Y), right view
plate_thk = 5       # mm, overall thickness (Z), front view
hole_dia = 6        # mm, blind hole diameter (callout: dia 6, depth 2)
hole_depth = 2      # mm, blind hole depth from top face
hole_x = 40         # mm, hole center from left edge (top view) -> centered
hole_y = 30         # mm, hole center from front edge (right view) -> centered

with BuildPart() as bp:
    # Base plate, centered on origin, top face at +Z = plate_thk/2
    Box(plate_len, plate_wid, plate_thk)
    # Blind hole from the top face, centered in plan
    with Locations((hole_x - plate_len / 2, hole_y - plate_wid / 2, plate_thk / 2)):
        Cylinder(
            radius=hole_dia / 2,
            height=hole_depth,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
            mode=Mode.SUBTRACT,
        )

part = bp.part
export_step(part, "output.step")
