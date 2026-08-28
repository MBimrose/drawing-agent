# std02_notchplate — agentic final (cand 1), IoU 0.971
from build123d import *

# --- Named dimensions read from the drawing (all mm) ---
left_margin = 25    # mm, X chain segment 1 (left edge to notch)
notch_width = 31    # mm, X chain segment 2 (notch width)
right_margin = 27   # mm, X chain segment 3 (notch to right edge)
overall_D = 55      # mm, overall Y depth (printed overall)
thickness = 8       # mm, Z thickness (Front / Right views)
notch_depth = 19    # mm, notch depth from front (-Y) edge
hole_dia = 8        # mm, 2X Ø8 THRU
hole_side_off = 12.5  # mm, hole center offset from side edges (symmetric, undimensioned)
hole_back_off = 12.5  # mm, hole center offset from back edge (undimensioned)

# --- Derived values ---
overall_W = left_margin + notch_width + right_margin  # = 83 mm, matches printed overall
hole_xs = [hole_side_off, overall_W - hole_side_off]
hole_y = overall_D - hole_back_off

with BuildPart() as bp:
    # Base plate, corner at origin: x 0..83, y 0..55, z 0..8
    Box(overall_W, overall_D, thickness,
        align=(Align.MIN, Align.MIN, Align.MIN))

    # Through-notch cut from the front edge (full Z thickness)
    with Locations((left_margin, 0, 0)):
        Box(notch_width, notch_depth, thickness,
            align=(Align.MIN, Align.MIN, Align.MIN),
            mode=Mode.SUBTRACT)

    # 2X Ø8 through-holes
    with Locations([(x, hole_y, 0) for x in hole_xs]):
        Cylinder(radius=hole_dia / 2, height=thickness,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
