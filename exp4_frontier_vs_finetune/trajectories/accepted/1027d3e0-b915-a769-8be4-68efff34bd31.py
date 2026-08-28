# 1027d3e0-b915-a769-8be4-68efff34bd31 — agentic final (cand 1), IoU 1.000
from build123d import *

# ---- Dimensions read from the drawing ----
L  = 80  # mm — overall length (X), from top/front views
T  = 8   # mm — overall thickness (Y), from right side view
H  = 40  # mm — overall height (Z), from front/right views
C2 = 2   # mm — 45° chamfer called out "C2" on all bottom perimeter edges

with BuildPart() as bp:
    # Base plate centered on origin (orientation: X = length, Y = thickness, Z = height)
    Box(L, T, H)

    # C2 chamfer around the entire bottom edge perimeter
    bottom_face = bp.faces().sort_by(Axis.Z)[0]
    chamfer(bottom_face.edges(), length=C2)

part = bp.part
export_step(part, "output.step")
