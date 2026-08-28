# hard00_steps3 — agentic final (cand 1), IoU 1.000
from build123d import *

# ---- dimensions read from the drawing ----
w_high = 28   # mm  X width of tallest step (left segment in Front view)
w_mid  = 21   # mm  X width of middle step
w_low  = 17   # mm  X width of lowest step (right segment in Front view)
depth  = 36   # mm  Y depth (overall in Top and Right views)

h_base = 10   # mm  height of lowest step (base layer, z 0..10)
h_mid  = 13   # mm  middle riser (z 10..23)
h_top  = 15   # mm  top riser (z 23..38)

# ---- derived extents ----
W     = w_high + w_mid + w_low   # 28+21+17 = 66 mm total X
H     = h_base + h_mid + h_top   # 10+13+15 = 38 mm total Z
x_mid = w_high + w_mid           # 49 mm: X extent that reaches the middle height
z_mid = h_base                   # 10 mm: top of base layer
z_top = h_base + h_mid           # 23 mm: top of middle layer

with BuildPart() as bp:
    # base layer: full footprint, height of the lowest step
    Box(W, depth, h_base, align=(Align.MIN, Align.MIN, Align.MIN))
    # second layer: only under the high + middle steps
    with Locations((0, 0, z_mid)):
        Box(x_mid, depth, h_mid, align=(Align.MIN, Align.MIN, Align.MIN))
    # third layer: only under the highest step
    with Locations((0, 0, z_top)):
        Box(w_high, depth, h_top, align=(Align.MIN, Align.MIN, Align.MIN))

part = bp.part
export_step(part, "output.step")
