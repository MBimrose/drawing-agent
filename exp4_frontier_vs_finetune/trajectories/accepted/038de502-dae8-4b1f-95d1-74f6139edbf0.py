# 038de502-dae8-4b1f-95d1-74f6139edbf0 — agentic final (cand 1), IoU 1.000
import math
from build123d import *

# ---------- dimensions read from the drawing ----------
plate_w  = 80.0   # mm overall width  (X) = 40 + 40 (edge -> centreline -> edge)
plate_d  = 80.0   # mm overall depth  (Y) = 40 + 40 (square plate, side view 40 to centreline)
thk      = 5.0    # mm plate thickness (front / right views)
corner_r = 4.0    # mm corner fillets, note "4x R4"
slot_w   = 40.0   # mm central slot width  = 2 x 20 (centred on vertical centreline)
slot_h   = 15.0   # mm central slot height (dimension across slot edges)
hole_d   = 5.0    # mm hole diameter, callout "8x ⌀5 THRU"
bc_d     = 60.0   # mm bolt-circle diameter, "... EQ SP ON ⌀60 BC"
n_holes  = 8      # eight holes, equally spaced (0°, 45°, ... as drawn)

bc_r = bc_d / 2.0  # mm bolt-circle radius

with BuildPart() as bp:
    with BuildSketch():
        # plate outline with R4 rounded corners
        Rectangle(plate_w, plate_d)
        fillet(vertices(), radius=corner_r)
        # central rectangular through-slot
        Rectangle(slot_w, slot_h, mode=Mode.SUBTRACT)
        # 8x ⌀5 through-holes equally spaced on the ⌀60 bolt circle
        with PolarLocations(bc_r, n_holes):
            Circle(hole_d / 2.0, mode=Mode.SUBTRACT)
    extrude(amount=thk)

part = bp.part
export_step(part, "output.step")
