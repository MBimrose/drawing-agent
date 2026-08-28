# 104587fa-61ef-cd7d-02d5-4978341a3bf6 — agentic final (cand 1), IoU 1.000
from build123d import *

# ---------- Dimensions read from the drawing ----------
disc_diameter = 80         # mm  overall diameter (FRONT "⌀80"; TOP & SECTION radius "40")
plate_thickness = 5        # mm  disc thickness (FRONT view)
hole_diameter = 4          # mm  hole diameter   (callout: 12× ⌀4)
hole_depth = 2             # mm  blind hole depth (callout: ↓ 2)
hole_count = 12            #     hole count      (callout: 12×)
bolt_circle_diameter = 60  # mm  bolt circle     (callout: ON ⌀60 BC)

# ---------- Derived values ----------
disc_radius = disc_diameter / 2                # mm
hole_radius = hole_diameter / 2                # mm
bolt_circle_radius = bolt_circle_diameter / 2  # mm

with BuildPart() as bp:
    # Base disc — axis along Z so the Top view is the XY plane
    Cylinder(radius=disc_radius, height=plate_thickness)

    # 12 blind holes drilled from the top face, equally spaced on the Ø60 BC
    top_face = bp.faces().sort_by(Axis.Z)[-1]
    with Locations(top_face):
        with PolarLocations(radius=bolt_circle_radius, count=hole_count):
            Hole(radius=hole_radius, depth=hole_depth)

part = bp.part
export_step(part, "output.step")
