# std07_lbracket — accepted trajectory plan

Reading the views:
- **Top view (left):** overall rectangle 83 (X) × 40 (Y). A vertical line 11 mm from the left end (83 − 72) marks the near face of the vertical wall; the wall occupies the left end. A ⌀8 circle (boss) sits centered in Y (20) and 63 mm from the left end (≈20 from the right end, read from the view).
- **Right view (middle):** overall height 60 (Z). A horizontal line 49 mm below the top = top of the base plate → plate thickness = 60 − 49 = 11. A small 8 mm dimension = height of the cylindrical boss above the plate.
- **ISO:** confirms L-shaped bracket: horizontal base plate with a small cylindrical boss on top, and a vertical wall at one end.

Dimension chains:
- X: overall 83 = wall thickness (83 − 72 = 11) + base length 72.
- Z: overall 60 = 49 (wall top → plate top) + 11 (plate thickness).
- Y: overall 40 (depth), boss centered at 20.

Features:
1. Base plate 83 × 40 × 11.
2. Vertical wall 11 (X) × 40 (Y) × 60 (Z) at the left end.
3. Cylindrical boss ⌀8 × 8 high on the plate top at (63, 20).

---

Reading the views (unchanged):
- **Top view (left):** overall rectangle 83 (X) × 40 (Y). A vertical line 11 mm from the left end (83 − 72) marks the near face of the vertical wall; the wall occupies the left end. A ⌀8 circle (boss) sits centered in Y (20) and 63 mm from the left end.
- **Right view (middle):** overall height 60 (Z). A horizontal line 49 mm below the top = top of the base plate → plate thickness = 60 − 49 = 11. A small 8 mm dimension = height of the cylindrical boss above the plate.
- **ISO:** confirms L-shaped bracket: horizontal base plate with a small cylindrical boss on top, and a vertical wall at one end.

Dimension chains:
- X: overall 83 = wall thickness (83 − 72 = 11) + base length 72.
- Z: overall 60 = 49 (wall top → plate top) + 11 (plate thickness).
- Y: overall 40 (depth), boss centered at 20.

Features:
1. Base plate 83 × 40 × 11.
2. Vertical wall 11 (X) × 40 (Y) × 60 (Z) at the left end.
3. Cylindrical boss ⌀8 × 8 high on the plate top at (63, 20).

Fix: `Locations` must receive a tuple of numbers, not a formatted string. Use `Locations((boss_x, boss_y, plate_t))`.