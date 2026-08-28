# 00d1e3d6-db1e-758d-94e6-76e246cf7349 — agentic final (cand 2), IoU 0.998
from build123d import *

# ---- dimensions read from drawing ----
edge_to_first_hole = 16   # mm, left edge to first hole center (top view)
hole_spacing = 12         # mm, "4x 12" spacing between the 5 holes
hole_count = 5            # "5x" holes
hole_diameter = 5         # mm, ⌀5
hole_depth = 4.5          # mm, blind depth from top face (↓ 4.5)
plate_thickness = 6       # mm, front view overall height
hole_row_offset = 40      # mm, hole row from edge (right view)
chamfer_len = 0.5         # mm, C0.5 chamfer on top perimeter edges

# ---- derived overall sizes ----
plate_width = 2 * edge_to_first_hole + (hole_count - 1) * hole_spacing  # 16+48+16 = 80 mm
plate_depth = 2 * hole_row_offset                                       # 40*2 = 80 mm

# hole X positions, plate centered on origin
hole_xs = [edge_to_first_hole + i * hole_spacing - plate_width / 2
           for i in range(hole_count)]  # -24, -12, 0, 12, 24

with BuildPart() as bp:
    # base plate 80 x 80 x 6
    with BuildSketch():
        Rectangle(plate_width, plate_depth)
    extrude(amount=plate_thickness)

    # 5 blind holes ⌀5 x 4.5 deep from the top face
    with Locations([(x, 0, plate_thickness) for x in hole_xs]):
        Cylinder(radius=hole_diameter / 2,
                 height=hole_depth,
                 align=(Align.CENTER, Align.CENTER, Align.MAX),
                 mode=Mode.SUBTRACT)

    # C0.5 chamfer on top perimeter edges (linear edges at top Z only)
    top_edges = bp.edges().filter_by(GeomType.LINE).group_by(Axis.Z)[-1]
    chamfer(top_edges, length=chamfer_len)

part = bp.part
export_step(part, "output.step")
