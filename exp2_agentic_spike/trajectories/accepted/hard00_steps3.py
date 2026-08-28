# hard00_steps3 — agentic final (cand 2), IoU 1.000
from build123d import *

# ---------------- dimensions read from the drawing ----------------
step1_len = 28   # mm - X length of tallest (left) section  (Front/Top chain)
step2_len = 21   # mm - X length of middle section          (Front/Top chain)
step3_len = 17   # mm - X length of lowest (right) section  (Front/Top chain)
depth     = 36   # mm - Y depth, overall (Top view and Right view)
tier1_h   = 10   # mm - height of bottom tier (Front/Right Z chain)
tier2_h   = 13   # mm - added height of middle tier (Front/Right Z chain)
tier3_h   = 15   # mm - added height of top tier (Front/Right Z chain)

# ---------------- derived overall extents ----------------
total_len = step1_len + step2_len + step3_len   # 28 + 21 + 17 = 66 mm (X)
total_h   = tier1_h + tier2_h + tier3_h         # 10 + 13 + 15 = 38 mm (Z)

with BuildPart() as bp:
    # bottom tier: full 66 x 36 footprint, z = 0..10
    Box(total_len, depth, tier1_h,
        align=(Align.MIN, Align.MIN, Align.MIN))
    # middle tier: covers tall + middle sections (X 0..49), z = 10..23
    with Locations((0, 0, tier1_h)):
        Box(step1_len + step2_len, depth, tier2_h,
            align=(Align.MIN, Align.MIN, Align.MIN))
    # top tier: covers tall section only (X 0..28), z = 23..38
    with Locations((0, 0, tier1_h + tier2_h)):
        Box(step1_len, depth, tier3_h,
            align=(Align.MIN, Align.MIN, Align.MIN))

# bind the finished solid (not the builder) to `part`
part = bp.part

export_step(part, "output.step")
