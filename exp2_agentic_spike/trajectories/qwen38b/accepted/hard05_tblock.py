# hard05_tblock — agentic final (cand 5), IoU 1.000
# Hub Adapter (T-plate) - build123d reconstruction
from build123d import *

# --- Dimensions read from the drawing ---
stem_width   = 29.0   # mm, Top/Front: stem width (X)
overhang     = 17.0   # mm, Top/Front: side overhang (X), right; left symmetric
crossbar_dep = 22.0   # mm, Top/Right: crossbar depth (Y)
stem_dep     = 33.0   # mm, Top/Right: stem depth (Y)
thickness    = 11.0   # mm, Right: plate thickness (Z)

# --- Derived values ---
overall_width = stem_width + 2 * overhang      # 63 mm (X)
overall_depth = crossbar_dep + stem_dep        # 55 mm (Y)

with BuildPart() as hub:
    # Crossbar: full width, at the back end (top of the Top view)
    Box(overall_width, crossbar_dep, thickness,
        align=(Align.CENTER, Align.MIN, Align.CENTER))
    # Stem: narrow, centered in X, projecting to the front end
    Box(stem_width, stem_dep, thickness,
        align=(Align.CENTER, Align.MAX, Align.CENTER))

part = hub.part
export_step(part, "output.step")
