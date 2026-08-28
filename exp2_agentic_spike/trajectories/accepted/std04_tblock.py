# std04_tblock — agentic final (cand 3), IoU 0.860
from build123d import *

# ---- Dimensions read from the drawing ----
overall_width = 70.0      # mm  X overall (Top & Front views)
crossbar_depth = 24.0     # mm  Y depth of the cross bar (Top & Right views)
stem_length = 35.0        # mm  Y length of the stem (Top & Right views)
stem_side_margin = 28.0   # mm  X distance from each side edge to the stem (Top & Front views)
part_height = 17.0        # mm  Z overall height (Front & Right views)

# ---- Derived values ----
overall_depth = crossbar_depth + stem_length          # 59 mm, matches printed overall
stem_width = overall_width - 2 * stem_side_margin     # 14 mm, stem centered in X

with BuildPart() as bp:
    # Cross bar: full 70 mm width, 24 mm deep, at the back (+Y) end of the plan
    with Locations((0, stem_length, 0)):
        Box(overall_width, crossbar_depth, part_height,
            align=(Align.CENTER, Align.MIN, Align.MIN))
    # Stem: 14 mm wide, centered in X, running from the front (-Y) end to the cross bar
    Box(stem_width, stem_length, part_height,
        align=(Align.CENTER, Align.MIN, Align.MIN))

# Extract the finished solid from the builder
part = bp.part

export_step(part, "output.step")
