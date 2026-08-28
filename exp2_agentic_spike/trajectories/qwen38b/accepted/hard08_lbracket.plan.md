# hard08_lbracket — accepted trajectory plan

Reading the views:
- **Top view** (XY): rectangle 80 mm (X) × 45 mm (Y). X is given as a chain: 12 (left segment, the vertical plate thickness) + 68 (plate face to right edge) = 80 overall. A ⌀7 circle sits centered in Y, ~19 mm from the right edge.
- **Right view** (YZ, seen from +X): rectangle 45 wide (Y, matches Top) × 51 tall (Z, overall height). A single horizontal line near the bottom = top face of the base plate (plate thickness ≈ 12, same as the vertical plate). No vertical line → the vertical plate spans the full 45 depth, so it must be at the X-end, not the Y-end.
- **ISO**: L-bracket — horizontal base plate with a vertical plate at one end, and a small raised cylindrical boss (the "hub") on the base plate away from the vertical plate.

Dimension chains:
- X: 12 + 68 = 80 (overall width)
- Y: 45 (overall depth, Top and Right agree)
- Z: 51 (overall height, Right view); base strip ≈ 12.

Feature list:
1. Base plate: 80 × 45 × 12, Z 0–12.
2. Vertical plate: 12 (X) × 45 (Y) × 51 (Z), at X 0–12, full depth.
3. Boss: ⌀7 cylinder on top of base, centered in Y (22.5), 19 mm from right edge (X = 61), height 12 (not dimensioned; taken from ISO proportion, assumed equal to plate thickness).

---

Reading unchanged (L-bracket: base plate 80×45×12, vertical plate 12×45×51 at left end, ⌀7 boss on base at X=61, Y=22.5). The only problem was API: build123d 0.10 primitives do not accept a `pos` keyword — positioning must be done with a `Locations(...)` context. I therefore wrap the boss cylinder in `Locations((boss_x, boss_y, t_base))` and use `align=(CENTER, CENTER, MIN)` so its axis is centered in XY at that point and its base sits on the top of the base plate. The two `Box` calls already used only the valid `align` argument.

---

Re‑reading the height chain (the only error in my first model):
- **Right view**: the rectangle is split by a horizontal line near the bottom. The "51" dimension spans the *upper* region (top edge → base‑top line) and the "12" dimension spans the *lower* strip (base‑top line → bottom edge). So 51 is the vertical plate height **above** the base, and the base thickness is 12. Overall height = 51 + 12 = **63**.
- **Front view** confirms this: the "51" arrow runs from the top edge down to the inner corner (base‑top line), and "68" runs from the inner vertical line to the right edge, "12" is the vertical‑plate thickness.
- **Top view**: 12 (left strip) + 68 = 80 overall X; 45 overall Y; ⌀7 boss circle, undimensioned in X (placed ≈19 mm from the right edge to match the drawing), centered in Y.

So my previous solid was too short (overall 51 instead of 63). Corrected extents: X = 12 + 68 = 80, Y = 45, Z = 51 + 12 = 63.

Feature list (corrected):
1. Base plate: 80 × 45 × 12 (Z 0–12).
2. Vertical plate: 12 × 45 × 63 (Z 0–63) at X 0–12, full depth (51 above the base top).
3. Boss: ⌀7 cylinder, height 12 (undimensioned, matched to ISO/Front proportion), centered in Y (22.5), X = 61, sitting on the base top (Z 12–24).