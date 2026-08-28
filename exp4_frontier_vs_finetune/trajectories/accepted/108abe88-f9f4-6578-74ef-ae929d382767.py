# 108abe88-f9f4-6578-74ef-ae929d382767 — agentic final (cand 2), IoU 0.999
from build123d import *

# ---- Dimensions read from drawing ----
bar_width = 50    # mm - overall X width of cross bar (top/front views)
total_depth = 42  # mm - overall Y depth (right view)
bar_depth = 12    # mm - Y thickness of cross bar (right view)
stem_width = 10   # mm - X width of stem, centered (front view)
height = 80       # mm - overall Z height (front/right views)
chamfer_len = 1   # mm - C1 chamfer on the four cross-bar corners

# ---- Derived ----
stem_depth = total_depth - bar_depth  # mm - stem length in Y = 42 - 12 = 30

with BuildPart() as bp:
    # T profile on the XY plane (top view): bar at back (+Y), stem at front (-Y)
    with BuildSketch(Plane.XY):
        with Locations((0, stem_depth + bar_depth / 2)):   # cross bar, Y in [30, 42]
            Rectangle(bar_width, bar_depth)
        with Locations((0, stem_depth / 2)):               # stem, Y in [0, 30]
            Rectangle(stem_width, stem_depth)
    extrude(amount=height)  # Z from 0 to 80

    # C1 chamfers: the four vertical edges at the cross bar's outer corners (|X| = 25)
    bar_corner_edges = [
        e for e in bp.edges().filter_by(Axis.Z)
        if abs(abs(e.center().X) - bar_width / 2) < 1e-4
    ]
    chamfer(bar_corner_edges, chamfer_len)

part = bp.part
export_step(part, "output.step")
