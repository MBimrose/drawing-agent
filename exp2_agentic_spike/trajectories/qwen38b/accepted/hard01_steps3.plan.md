# hard01_steps3 — accepted trajectory plan

Reading the views:
- Top view: rectangle 77 wide (X) × 43 deep (Y). The X width is a component chain 25 + 34 + 18 = 77 (no overall given, so sum the chain). Two internal lines at x = 25 and x = 59 mark the step edges. Depth 43 is the overall Y.
- Front view (X–Z): stepped profile. Left segment (width 25) is highest; middle segment (width 34) is 13 mm lower; right segment (width 18) is a further 15 mm lower. So vertical drops: 13 (top block above middle) and 15 (middle above base). The base step height is not explicitly dimensioned; from the drawing proportions (Right view bottom band ≈ half the 15 mm band) it is taken as 8 mm. Total height = 8 + 15 + 13 = 36.
- Right view (Y–Z): full depth 43 with horizontal lines at the two step heights, confirming 13 and 15 bands and that every step spans the full 43 depth.
- ISO: confirms a three-step block descending in the X direction, full depth.

Feature list:
- Base block: 77 (X) × 43 (Y) × 8 (Z).
- Middle block: 59 (X = 25+34) × 43 (Y) × 15 (Z), stacked on base over the left 59 mm.
- Top block: 25 (X) × 43 (Y) × 13 (Z), stacked on middle over the left 25 mm.
- No holes, fillets, or chamfers dimensioned.

Dimension chains:
- X: 25 + 34 + 18 = 77 (overall width).
- Y: 43 (overall depth, given).
- Z: 8 + 15 + 13 = 36 (overall height).

---

Diagnosis of the mismatch:
- The attached renders (Top / Front / Right) show a TWO‑step solid: Front = one tall left region + one short right region; Right = two horizontal bands; Top = a single vertical split line. The reported solid (77 × 43 × 15, 8 planar faces, volume 44247 mm³) is exactly the union of three boxes that all collapsed to z = 0 (the `.translate(...)` chained on each `Box` did not move the object registered in the part, so the part became a 59‑wide × 15‑tall block over an 18‑wide × 8‑tall block).
- The ORIGINAL drawing (first sheet) is a THREE‑step block: width chain 25 + 34 + 18 = 77 (X), depth 43 (Y), and three stacked heights in Z — top rise 13, middle rise 15, and a base step (undimensioned; read from the view proportions as 8). Total height = 8 + 15 + 13 = 36. The Front view must show three levels and the Right view three bands.

Fix:
- Keep the same named dimensions.
- Build the three boxes with explicit stacking using `Locations(...)` so each box's MIN corner is placed at the correct Z (0, h_base, h_base + h_mid). This yields a true three‑step solid: 77 × 43 × 36, 10 planar faces.

Feature list (corrected):
- Base: 77 (X) × 43 (Y) × 8 (Z), z = 0.
- Middle: 59 (X = 25+34) × 43 (Y) × 15 (Z), z = 8.
- Top: 25 (X) × 43 (Y) × 13 (Z), z = 23.
- No holes / fillets / chamfers.