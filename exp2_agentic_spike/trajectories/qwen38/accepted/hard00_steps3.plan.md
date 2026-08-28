# hard00_steps3 — accepted trajectory plan

Reading the views:
- **Top view:** rectangle 66 wide × 36 deep, with two internal lines at x=28 and x=49 (chain 28 + 21 + 17 = 66). Depth dimension = 36.
- **Front view (XZ):** a 3-step descending staircase. Horizontal chain 28 + 21 + 17 = 66 (overall X). Vertical chain on the right: 15 + 13 + 10 = 38 (overall Z). So the left block (x 0–28) is 38 tall, the middle block (x 28–49) is 23 tall, the right block (x 49–66) is 10 tall.
- **Right view (YZ):** full rectangle 36 wide × 38 tall with horizontal lines at the step levels (15, 13, 10) — confirms depth 36 and total height 38.
- **ISO:** confirms a three-step staircase prism of uniform depth.

Dimension chains:
- X: 28 + 21 + 17 = 66 (overall width)
- Y: 36 (overall depth)
- Z: 15 + 13 + 10 = 38 (overall height); step heights 38, 23, 10.

Feature list: three rectangular steps (prisms extruded 36 in Y):
1. x 0–28, z 0–38
2. x 28–49, z 0–23
3. x 49–66, z 0–10
No holes, no fillets/chamfers dimensioned.

---

Reading unchanged from before:
- **Top view:** rectangle 66 wide × 36 deep; internal lines at x=28 and x=49 (chain 28 + 21 + 17 = 66).
- **Front view (XZ):** 3-step descending staircase. X chain 28 + 21 + 17 = 66; Z chain 15 + 13 + 10 = 38. Step heights: tall=38, middle=23, low=10.
- **Right view (YZ):** 36 × 38 rectangle with step lines — confirms depth 36, height 38.
- **ISO:** three-step staircase prism, uniform depth.

Fix: the `BuildPart` context manager yields the builder, not the solid. Bind the finished solid via `m.part` to the variable `part` before exporting.

---

The previous script only produced a single 28×36×38 box (volume 38304) because `Box(...).translate(...)` inside a `BuildPart` context registers only the *untranslated* box; the translated copies were discarded, so all three stacked at the origin and unioned into one tall block. The rendered Top/Front/Right are therefore plain rectangles with no step edges, and the X extent is 28 instead of the required 66.

Correct reading (unchanged):
- X chain: 28 + 21 + 17 = 66 (overall width)
- Y: 36 (depth)
- Z chain: 15 + 13 + 10 = 38 (overall height); step heights 38 / 23 / 10

Fix: position each step with the `Locations` context manager (the idiomatic build123d pattern that actually places the object), inside a single `BuildPart`. Expected result: bounding box 66 × 36 × 38, three-step staircase, volume = 28·36·38 + 21·36·23 + 17·36·10 = 61812 mm³.

---

Diagnosis of the bad render: `Box` is centered on its location by default (`align=Align.CENTER`). With my `Locations` at x = 0 / 28 / 49 the three boxes actually spanned −14..14, 17.5..38.5, 40.5..57.5 → gaps between them, 3 separate solids, and an overall X extent of 71.5 (not 66). The Front/Top renders confirm the disconnected rectangles.

Fix: give each `Box` `align=(Align.MIN, Align.MIN, Align.MIN)` so its minimum corner sits at the `Locations` offset. Then the steps are contiguous (0..28, 28..49, 49..66) and union into one solid: bounding box 66 × 36 × 38, volume 61812 mm³, three-step staircase matching the drawing.