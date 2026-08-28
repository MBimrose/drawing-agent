# 00d1e3d6-db1e-758d-94e6-76e246cf7349 — agentic final (cand 1), IoU 0.998
from build123d import *

# ---------- dimensions read from the drawing ----------
edge_to_first_hole = 16   # mm - top view: left edge to 1st hole centre
hole_pitch = 12           # mm - top view: "4x 12" between adjacent hole centres
hole_count = 5            #     - callout "5x ⌀5 ↓ 4.5"
hole_diameter = 5         # mm - hole callout
hole_depth = 4.5          # mm - blind depth from top face (Section A-A: not thru)
edge_to_hole_row = 40     # mm - side view: plate edge to hole-row centreline
plate_thickness = 6       # mm - front view
top_chamfer = 0.5         # mm - "C0.5" on top corners (front & side views)

# ---------- derived overall sizes ----------
# X chain: 16 + 4*12 + 16 (right margin mirrors the left) = 80
plate_length = 2 * edge_to_first_hole + (hole_count - 1) * hole_pitch
# Y: hole row centred, 40 each side -> 80 (square plate, per top/ISO views)
plate_width = 2 * edge_to_hole_row

with BuildPart() as bp:
    # base plate 80 x 80 x 6, bottom face on Z=0
    Box(plate_length, plate_width, plate_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # C0.5 x 45 deg chamfer around the top perimeter edges
    chamfer(bp.edges().group_by(Axis.Z)[-1], top_chamfer)

    # five blind holes ⌀5 x 4.5 deep from the top face, row centred in Y
    x_first = -plate_length / 2 + edge_to_first_hole
    with Locations([(x_first + i * hole_pitch, 0, plate_thickness)
                    for i in range(hole_count)]):
        Cylinder(hole_diameter / 2, hole_depth,
                 align=(Align.CENTER, Align.CENTER, Align.MAX),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
