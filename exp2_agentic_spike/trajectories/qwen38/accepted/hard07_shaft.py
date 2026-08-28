# hard07_shaft — agentic final (cand 2), IoU 1.000
from build123d import BuildPart, Cylinder, Locations, Align, export_step

# ---- Dimensions read from the drawing (mm) ----
base_d = 42.0   # mm  base cylinder outer diameter (Top view outer circle)
mid_d  = 22.0   # mm  middle cylinder outer diameter (Top view middle circle)
top_d  = 16.0   # mm  top cylinder outer diameter (Top view inner circle)

base_h = 26.0   # mm  base cylinder height (Front/Right bottom segment)
mid_h  = 18.0   # mm  middle cylinder height (Front/Right middle segment)
top_h  = 13.0   # mm  top cylinder height (Front/Right top segment)

# Derived values
base_r = base_d / 2.0   # mm
mid_r  = mid_d  / 2.0   # mm
top_r  = top_d  / 2.0   # mm
total_h = base_h + mid_h + top_h   # mm  = 57, overall height

# ---- Build the stacked concentric cylinders (axis = Z, base bottom at Z=0) ----
C = Align.CENTER
M = Align.MIN
with BuildPart() as p:
    with Locations((0, 0, 0.0)):
        Cylinder(base_r, base_h, align=(C, C, M))
    with Locations((0, 0, base_h)):
        Cylinder(mid_r, mid_h, align=(C, C, M))
    with Locations((0, 0, base_h + mid_h)):
        Cylinder(top_r, top_h, align=(C, C, M))

part = p.part

export_step(part, "output.step")
