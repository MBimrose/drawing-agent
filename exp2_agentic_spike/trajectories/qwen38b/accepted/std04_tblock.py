# std04_tblock — agentic final (cand 3), IoU 0.877
# Shaft collar - centered T-shaped block (build123d 0.10)
from build123d import *

# ---- Dimensions read from the drawing (mm) ----
overall_y      = 59.0    # mm, overall depth (Top view overall / Right view overall)
upper_depth    = 24.0    # mm, back bar depth (Top view top dim / Right view 24)
left_overhang  = 28.0    # mm, side edge to stem left edge (Top & Front left dim)
stem_width     = 26.0    # mm, stem width (Top & Front middle dim)
right_overhang = left_overhang  # mm, stem centered -> right overhang = left
thickness      = 17.0    # mm, uniform thickness (Front & Right height dim)

# ---- Derived values ----
lower_depth = overall_y - upper_depth                  # 35 mm, stem depth (chain 24 + 35 = 59)
overall_x   = left_overhang + stem_width + right_overhang  # 82 mm (28 + 26 + 28)

# ---- Build the solid ----
with BuildPart() as mp:
    # Back bar (top of Top view), full width
    with Locations((0, lower_depth, 0)):
        Box(overall_x, upper_depth, thickness,
            align=(Align.MIN, Align.MIN, Align.CENTER))
    # Front stem (bottom of Top view), centered in X
    with Locations((left_overhang, 0, 0)):
        Box(stem_width, lower_depth, thickness,
            align=(Align.MIN, Align.MIN, Align.CENTER))

# Bind the finished solid to `part`
part = mp.part

export_step(part, "output.step")
