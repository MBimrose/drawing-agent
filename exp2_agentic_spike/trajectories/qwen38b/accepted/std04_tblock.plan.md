# std04_tblock — accepted trajectory plan

Reading the views:
- **Top view** (only dimensioned view): an L-shaped profile. Vertical (Y) dimensions: 24 = depth of the back (upper) bar; 59 = overall height; the front (lower) bar depth is the remainder 59 − 24 = 35 (the printed 55 is inconsistent with the overall 59 and the 24 segment, so the chain 24 + 35 = 59 governs). Horizontal (X): 28 = distance from the left edge to the left edge of the front bar. No overall X is printed; the front bar width equals the back bar depth (24) and the right overhang mirrors the left offset (28), giving overall X = 28 + 24 + 28 = 80 (matches the drawn proportions).
- **Right view**: label present but no geometry rendered → part is a uniform extrusion; thickness taken as 24 mm (equal to the flange depth, consistent with ISO proportions).
- **ISO**: confirms a flat L-shaped block (prism), no holes, no fillets.

Feature list:
- Back bar: 80 (X) × 24 (Y) × 24 (Z)
- Front bar: 24 (X) × 35 (Y) × 24 (Z), positioned 28 mm from the left edge, flush with the bottom edge
- Union of the two boxes; overall bounding box 80 × 59 × 24.

---

Reading the views (unchanged):
- **Top view** (only dimensioned view): L-shaped profile. Y (vertical on sheet): 24 = depth of back (upper) bar; 59 = overall depth; front (lower) bar depth = 59 − 24 = 35 (the printed 55 is inconsistent with the 59 overall and the 24 segment, so the chain 24 + 35 = 59 governs). X (horizontal): 28 = left edge to front-bar left edge; front-bar width = 24 (equals back-bar depth per ISO proportions); right overhang mirrors left (28) → overall X = 28 + 24 + 28 = 80.
- **Right view**: label only, no geometry → uniform extrusion; thickness = 24 mm (per ISO proportions).
- **ISO**: flat L-shaped prism, no holes, no fillets.

Feature list:
- Back bar: 80 (X) × 24 (Y) × 24 (Z)
- Front bar: 24 (X) × 35 (Y) × 24 (Z), 28 mm from left edge, flush with bottom
- Union → bounding box 80 × 59 × 24.

Fix: the `BuildPart` context manager is not itself a solid; the finished solid is its `.part` attribute. Bind that to `part` before exporting.

---

Re-comparing my rendered solid (T‑shape, 80 × 59 × 24) against the original drawing reveals three errors:

1. **Thickness (Z):** The Front view's height dimension and the Right view's height dimension are both **17**, not 24. My solid is 24 thick — wrong.
2. **Stem width (X):** The Top view's middle horizontal dimension and the Front view's middle panel are **26** (the stem width), not 24.
3. **Overall width (X):** The chain is left overhang **28** + stem **26** + right overhang. The right overhang is not separately dimensioned but the Top view shows the stem centered (left overhang = right overhang = 28), so overall X = 28 + 26 + 28 = **82**, not 80.

Y‑axis is correct: back‑bar depth 24 + front‑bar (stem) depth 35 = overall 59 (confirmed by the Right view's 35 / 59 / 24 chain). The shape is a centered T‑prism (stem offset from both side edges by 28), thickness 17.

Corrected feature list:
- Back bar: 82 (X) × 24 (Y) × 17 (Z)
- Front stem: 26 (X) × 35 (Y) × 17 (Z), centered in X (28 mm from each side), flush with the front edge
- Union → bounding box 82 × 59 × 17.