# 080b2e00-c9be-606a-3207-08419028ffd0 — agentic final (cand 1), IoU 0.877
from build123d import *

# ================= Dimensions (from drawing) =================
plate_X = 60.0      # mm - overall width (top & front views)
plate_Y = 45.0      # mm - overall depth (right view)
plate_Z = 5.0       # mm - plate thickness (front & right views)
corner_R = 4.0      # mm - 4x R4 corner fillets (plan)
top_chamfer = 0.8   # mm - C0.8 chamfer on top perimeter edges

slot_X = 30.0       # mm - through-slot length (X), spans 15..45 -> centered
slot_Y = 10.0       # mm - through-slot width (Y), centered: (45-10)/2 = 17.5/side

hole_dia = 4.0      # mm - 2x Ø4 THRU
hole_1_x = 20.0     # mm - left hole center from left edge
hole_2_x = 40.0     # mm - right hole center from left edge
hole_y = 15.0       # mm - hole centers from front edge (right view)

# Derived positions (part centered on origin)
hx1 = hole_1_x - plate_X / 2   # -10
hx2 = hole_2_x - plate_X / 2   # +10
hy = hole_y - plate_Y / 2      # -7.5 (toward front, -Y)

with BuildPart() as bp:
    # Base plate 60 x 45 with R4 rounded corners
    with BuildSketch():
        Rectangle(plate_X, plate_Y)
        fillet(vertices(), radius=corner_R)
    extrude(amount=plate_Z)

    # C0.8 chamfer on top outer perimeter (before openings are cut)
    chamfer(edges().group_by(Axis.Z)[-1], length=top_chamfer)

    # 30 x 10 through-slot, centered in X and Y
    with Locations((0, 0, plate_Z / 2)):
        Box(slot_X, slot_Y, plate_Z + 2, mode=Mode.SUBTRACT)

    # 2x Ø4 through-holes
    with Locations((hx1, hy, 0), (hx2, hy, 0)):
        Cylinder(radius=hole_dia / 2, height=plate_Z + 2, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
