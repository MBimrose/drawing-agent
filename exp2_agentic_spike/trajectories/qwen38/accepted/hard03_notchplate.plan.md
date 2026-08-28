# hard03_notchplate — accepted trajectory plan

**View reading:**
- **Top view:** Overall rectangle 72 (X) × 54 (Y). A rectangular notch is cut from the bottom (front) edge: it starts at X=24, is 20 wide (to X=44), and 16 deep from the front edge. Two ⌀8 through holes sit near the top edge, one near each side.
- **Front view:** Uniform height 14 across the full 72 width; vertical lines at X=24 and X=44 mark the notch side walls (no vertical step, so thickness is constant).
- **Right view:** 54 deep × 14 high rectangle, confirming depth and thickness.
- **ISO:** Confirms a flat, constant-thickness plate with a planar notch and two through holes.

**Dimension chains:**
- X (width): 24 + 20 + 28 = 72 (overall).
- Y (depth): 54 overall (single dimension, cross-checked in Right view).
- Z (thickness): 14 (Front and Right views).
- Notch: 20 wide × 16 deep, located 24 from the left edge, opening on the front (Y=0) edge.

**Features:**
1. Base plate 72 × 54 × 14.
2. Notch 20 × 16 × 14 removed from front edge between X=24 and X=44.
3. Two ⌀8 through holes, inset 12 mm from the left/right edges and 12 mm from the top edge → centers at (12, 42) and (60, 42).

---

**Views:** Top (XY), Front (XZ, from −Y), Right (YZ, from +X), ISO.

**Dimension chains:**
- X (width): 24 + 20 + 28 = 72 (overall).
- Y (depth): 54 (single overall dim, confirmed by Right view width).
- Z (thickness): 14 (Front & Right view heights).

**Features:**
1. Base plate 72 (X) × 54 (Y) × 14 (Z), origin at front‑left‑bottom.
2. Edge notch (slot through Z) on the front edge: 20 wide (X 24→44) × 16 deep (Y 0→16) × 14 thick. In Front view it shows only as the two vertical side‑wall lines at X=24,44 (material behind fills the silhouette); in Right view the silhouette stays a full 54×14 rectangle.
3. Two ⌀8 through‑holes, inset 12 from left/right edges and 12 from the top (back) edge → centers (12, 42) and (60, 42).

Cross‑checks: hole Y=42 clears notch top Y=16; front view full 72×14 rectangle with internal lines at 24/44; right view 54×14 — all consistent with a constant‑thickness plate.

---

**Views:** Top (XY), Front (XZ, from −Y), Right (YZ, from +X), ISO.

**Dimension chains:**
- X (width): 24 + 20 + 28 = 72 (overall).
- Y (depth): 54 (single overall dim, confirmed by Right view width).
- Z (thickness): 14 (Front & Right view heights).

**Features:**
1. Base plate 72 (X) × 54 (Y) × 14 (Z), origin at front‑left‑bottom.
2. Front‑edge notch (through Z): 20 wide (X 24→44) × 16 deep (Y 0→16) × 14 thick.
3. Two ⌀8 through‑holes, inset 12 from left/right edges and 12 from the back edge → centers (12, 42) and (60, 42).

**Fix from previous run:** the export must use the solid (`bp.part`), bound to `part`, not the `BuildPart` context object.