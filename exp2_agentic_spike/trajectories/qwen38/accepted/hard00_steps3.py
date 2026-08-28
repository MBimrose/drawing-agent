# hard00_steps3 — agentic final (cand 4), IoU 1.000
# HUB ADAPTER - three-step staircase block (build123d 0.10)
from build123d import *

# --- dimensions read from the drawing (mm) ---
seg1   = 28.0   # mm  X segment, tall step
seg2   = 21.0   # mm  X segment, middle step
seg3   = 17.0   # mm  X segment, low step
drop1  = 15.0   # mm  drop from top of tall step to middle step
drop2  = 13.0   # mm  drop from middle step to low step
drop3  = 10.0   # mm  height of low step
depth  = 36.0   # mm  overall depth (Y)

# --- derived values ---
H_high = drop1 + drop2 + drop3       # 38 mm height of tall step
H_mid  = drop2 + drop3               # 23 mm height of middle step
H_low  = drop3                       # 10 mm height of low step
x_mid  = seg1                        # 28 mm
x_low  = seg1 + seg2                 # 49 mm

# align each box so its min corner is at the location offset
min_align = (Align.MIN, Align.MIN, Align.MIN)

with BuildPart() as m:
    # tall step (left in Front view)
    with Locations((0.0, 0.0, 0.0)):
        Box(seg1, depth, H_high, align=min_align)
    # middle step
    with Locations((x_mid, 0.0, 0.0)):
        Box(seg2, depth, H_mid, align=min_align)
    # low step
    with Locations((x_low, 0.0, 0.0)):
        Box(seg3, depth, H_low, align=min_align)

# bind finished solid
part = m.part

export_step(part, "output.step")
