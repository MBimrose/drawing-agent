# 0feed9be-4eb8-0add-b7e8-b7225422d911 — agentic final (cand 2), IoU 0.897
from build123d import *

# --- Dimensions read from the drawing ---
od = 60.0            # mm  outer diameter (front view ⌀60; right view R30)
bore_dia = 40.0      # mm  through-bore diameter (front view ⌀40)
height = 76.0        # mm  overall height (front view)
rim_w = 5.0          # mm  outer rim width at top (top view "5")
recess_depth = 5.0   # mm  depth of top annular recess (step in front view / ISO band)
hole_dia = 5.0       # mm  hole diameter (callout: 2x ⌀5 THRU)
hole_spacing = 55.0  # mm  nominal hole center-to-center distance (top view "55")

# --- Derived values ---
recess_dia = od - 2 * rim_w   # mm  recess diameter = 50 (rim occupies R25-R30)

# The drawing's exact numbers put each ⌀5 hole tangent to BOTH the OD
# (27.5 + 2.5 = 30.0 = R30) and the recess wall (27.5 - 2.5 = 25.0 = R25).
# That line-contact tangency is non-manifold (non-watertight mesh, Y extent
# reading 59.98). Pull the centers in by a tiny clearance - far inside the
# ISO 2768-m tolerance on the "55" dimension - to get a clean solid.
clearance = 0.02                              # mm per side
hole_r = od / 2 - hole_dia / 2 - clearance    # mm  hole center radius = 27.48

with BuildPart() as bp:
    # Solid tube (axis along Z, base at Z=0)
    Cylinder(radius=od / 2, height=height,
             align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Through bore ⌀40
    Cylinder(radius=bore_dia / 2, height=height,
             align=(Align.CENTER, Align.CENTER, Align.MIN),
             mode=Mode.SUBTRACT)
    # Top annular recess ⌀50 x 5 deep (leaves 5 mm rim at full height)
    with Locations((0, 0, height - recess_depth)):
        Cylinder(radius=recess_dia / 2, height=recess_depth,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)
    # 2x ⌀5 through-holes on the X axis
    with Locations([(-hole_r, 0, 0), (hole_r, 0, 0)]):
        Cylinder(radius=hole_dia / 2, height=height,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
