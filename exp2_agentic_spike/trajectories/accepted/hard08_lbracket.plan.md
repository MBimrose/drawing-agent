# hard08_lbracket — accepted trajectory plan

**View reading:**
- **Top (XY, from +Z):** Rectangle 68 (X) × 46 (Y) with a ⌀7 circle (through-hole in the base). The 68 dimension runs from the wall's inner face to the free end; the wall strip (12) sits to its left, so the full footprint is 12 + 68 = 80 in X. The hole is centered in Y (46/2 = 23) and sits ≈19 mm from the free end (X = 80 − 19 = 61 from the wall's outer face).
- **Front (XZ, from −Y):** L-profile. Vertical leg at left: thickness 12, rising 51 above the base. Base: 68 long, 12 thick. Z chain: 12 + 51 = 63 total height. X chain: 12 + 68 = 80 total length. Dashed hidden lines in the base confirm the ⌀7 vertical hole at X ≈ 61.
- **Right (YZ, from +X):** Rectangle 46 (Y) × 63 (Z) with a horizontal edge line at Z = 12 (top of base), confirming the wall spans the full 46 width and the 51 + 12 height chain.
- **ISO:** Confirms L-bracket: full-width vertical plate at one end of a flat base, hole through the base.

**Dimension chains:**
- X (overall): 12 (wall) + 68 (base) = **80**
- Y (overall, given): **46**
- Z (overall): 12 (base) + 51 (wall) = **63**

**Features:**
1. Base plate: 80 × 46 × 12
2. Vertical wall: 12 thick × 46 wide × 51 tall, on top of base at the X = 0 end
3. Through-hole ⌀7 (vertical, through base) at (X=61, Y=23) — i.e., 19 mm from the free end, centered across the width

---

**Comparison of renders vs. drawing:**
- Extents: X = 12 + 68 = 80 ✓, Y = 46 ✓, Z = 12 + 51 = 63 ✓ — all match.
- L-profile in Front, full-width wall line at Z=12 in Right, wall strip in Top — all match.
- **Defect found:** the ⌀7 hole. In the drawing it is a THRU hole (solid visible circle in Top, hidden lines spanning the full 12 mm base thickness in Front). In my render the Top circle is shown as hidden (dotted) and the Front hidden lines only reach halfway up the base: build123d's `Cylinder` defaults to `align=Align.CENTER` on Z, so the 12 mm cylinder at z=0 spanned −6…+6 and only cut the lower half of the base (confirmed by volume: 72312 − π·3.5²·6 ≈ 72082, not the full-through 71850).
- Fix: cut the hole with `align=(Align.CENTER, Align.CENTER, Align.MIN)` at z=0 so it passes through the entire base thickness. Position unchanged: X = 80 − 19 = 61, Y = 46/2 = 23.