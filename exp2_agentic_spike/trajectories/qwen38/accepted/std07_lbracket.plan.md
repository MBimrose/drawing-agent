# std07_lbracket — accepted trajectory plan

Reading the views:
- **Top view** (XY, X right, Y up): overall rectangle 83 (X) × 40 (Y). A vertical line near the left edge splits it; the 72 dimension runs from that line to the right edge, so the left strip = 83 − 72 = **11**. A single circle (boss) sits on the right portion, centered in Y.
- **Right view** (YZ, Y right, Z up): full rectangle 40 (Y) × 60 (Z) with a horizontal line near the bottom. The 49 dimension runs from the top to that line, so the bottom strip = 60 − 49 = **11** (base thickness).
- **ISO**: an L‑bracket — a vertical wall at the left end (full depth, full height) plus a horizontal base plate extending to the right, with a small cylindrical boss on the base.

Dimension chains:
- X: overall 83 = wall 11 + base 72.
- Y (depth): 40.
- Z: overall 60 = base 11 + wall‑above‑base 49.

Features:
1. Base plate: 83 (X) × 40 (Y) × 11 (Z).
2. Vertical wall at left: 11 (X) × 40 (Y) × 60 (Z).
3. Boss cylinder on base: ⌀10 × 10 high, centered at Y = 20, X ≈ 63 (read from circle position; not explicitly dimensioned).

Construction: union of two boxes + one cylinder in a single BuildPart.

---

Reading (unchanged from before):
- **Top view** (XY): overall 83 (X) × 40 (Y); a vertical line at X = 83 − 72 = **11** separates the left wall strip from the 72‑long base; one boss circle on the base, centered in Y.
- **Right view** (YZ): overall 40 (Y) × 60 (Z); a horizontal line at Z = 60 − 49 = **11** is the base‑plate top.
- **ISO**: L‑bracket = left vertical wall (full depth/height) + horizontal base plate + small boss on the base.

Dimension chains: X: 83 = 11 (wall) + 72 (base). Y: 40. Z: 60 = 11 (base) + 49 (wall above base).

Features:
1. Base plate 83 × 40 × 11.
2. Left wall 11 × 40 × 60.
3. Boss ⌀10 × 10 at (X≈63, Y=20, on base top).

Construction fix: the previous `.align(...)` call is not available on the primitive in this build123d build, so each solid is positioned with a `Locations([Location(cx,cy,cz)])` context (placing the primitive's center at the computed corner‑derived center). This uses only `BuildPart`, `Locations`, `Box`, `Cylinder`.

---

Reading (unchanged):
- **Top view** (XY): overall 83 (X) × 40 (Y); vertical line at X = 83 − 72 = **11** separates the left wall strip from the 72‑long base; one boss circle on the base, centered in Y.
- **Right view** (YZ): overall 40 (Y) × 60 (Z); horizontal line at Z = 60 − 49 = **11** is the base‑plate top.
- **ISO**: L‑bracket = left vertical wall (full depth/height) + horizontal base plate + small boss on the base.

Dimension chains: X: 83 = 11 (wall) + 72 (base). Y: 40. Z: 60 = 11 (base) + 49 (wall above base).

Features:
1. Base plate 83 × 40 × 11.
2. Left wall 11 × 40 × 60.
3. Boss ⌀10 × 10 at (X≈63, Y=20, on base top).

Construction fix: this build123d build rejects `Location(x, y, z)` with three floats (and `.align` is unavailable), so each primitive is centered at the origin and then placed with `Locations([Location(Vector(cx, cy, cz))])`, which the `Location` constructor accepts as a single `Vector` translation.