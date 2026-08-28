# hard06_shaft — agentic final (cand 1), IoU 0.940
from build123d import *

# ---- Dimensions read from the drawing (all mm) ----
# Top view — concentric circles = the three tier diameters
base_dia = 42   # mm  bottom tier diameter ("Ø42" callout)
mid_dia  = 30   # mm  middle tier diameter ("Ø30" callout)
top_dia  = 18   # mm  top boss diameter  ("Ø18" callout)

# Front / Right views — vertical chain of tier heights
base_h = 28     # mm  bottom tier height
mid_h  = 21     # mm  middle tier height
top_h  = 11     # mm  top boss height

# Derived overall height: 28 + 21 + 11 = 60 (matches printed overall "60" in Right view)
total_h = base_h + mid_h + top_h

with BuildPart() as bp:
    # Tier 1 — base: Ø42 x 28, bottom face on Z=0
    Cylinder(radius=base_dia / 2, height=base_h,
             align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Tier 2 — middle: Ø30 x 21, stacked coaxially on tier 1
    with Locations((0, 0, base_h)):
        Cylinder(radius=mid_dia / 2, height=mid_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Tier 3 — top boss: Ø18 x 11, stacked coaxially on tier 2
    with Locations((0, 0, base_h + mid_h)):
        Cylinder(radius=top_dia / 2, height=top_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

part = bp.part
export_step(part, "output.step")
