# hard06_shaft — accepted trajectory plan

**View reading:**
- **Top view:** three concentric circles — ⌀42 (outer), ⌀30 (middle), ⌀18 (inner). These are the three coaxial cylindrical steps of the pump cover (axis vertical, Z).
- **Right view:** three stacked rectangles giving the step heights: bottom = 26, middle = 21, top = 11. Widths match the diameters (42 / 30 / 18).
- **Front view:** shows the top step, ⌀18 wide and 11 high, confirming the top cylinder.
- **ISO:** solid stepped cylinder, no holes, no fillets/chamfers.

**Dimension chains:**
- Z (height): 26 + 21 + 11 = 58 mm overall (component chain, no overall given).
- X/Y: overall extent = ⌀42 = 42 mm (single overall, consistent in Top and Right views).

**Feature list:**
1. Base cylinder: ⌀42 × 26 high, z = 0…26.
2. Middle cylinder: ⌀30 × 21 high, z = 26…47.
3. Top cylinder: ⌀18 × 11 high, z = 47…58.
No holes, notches, or fillets.

**Construction:** three centered cylinders translated to their base heights and unioned; axis along Z so Top view shows the circles.

---

Reading is unchanged (three coaxial stepped cylinders, axis vertical = Z):
- **Top:** ⌀42 / ⌀30 / ⌀18 concentric circles.
- **Right:** step heights 26 / 21 / 11 → overall Z = 26 + 21 + 11 = 58 mm.
- **Front:** top step ⌀18 × 11, consistent.

**Fix:** build123d 0.10 `Part` does not define the `|` (union) operator. I will build the solid inside a `BuildPart` context manager, where each placed `Cylinder` is added with the default `Mode.ADD`, producing a single fused solid. No other geometry changes.

---

Geometry reading is unchanged — three coaxial stepped cylinders, axis vertical (Z):
- **Top:** ⌀42 / ⌀30 / ⌀18 concentric circles.
- **Right:** step heights 26 / 21 / 11 → overall Z = 26 + 21 + 11 = 58 mm.
- **Front:** top step ⌀18 × 11, consistent.

**Fix:** In build123d 0.10 the `BuildPart` context manager exposes the result via the **property** `.part`, not a method. The previous run executed the `BuildPart` block fine and only failed on `pump_cover.part()` (calling a `Part`). I drop the parentheses: `part = pump_cover.part`. The three placed cylinders are unioned by the default `Mode.ADD` inside the context.

---

The previous solid came out as a **single** ⌀42 × 26 cylinder (bbox 42 × 42 × 26, one r21 cylindrical face) — only the base step survived. The middle (⌀30 × 21) and top (⌀18 × 11) cylinders were lost, so the Z extent is 26 instead of the required 26 + 21 + 11 = 58. The cause is the `BuildPart` auto‑add behavior in build123d 0.10 not capturing the `.translate()`‑chained parts reliably.

**Fix (no geometry change):** build the three coaxial cylinders as plain `Part` objects and combine them with the build123d union operator `+` (the `|` operator is not defined in this library, which was the original error). This is a pure boolean expression, fully deterministic, with no context‑manager auto‑add ambiguity.

- Base: ⌀42 (r21) × 26, center z = 13
- Middle: ⌀30 (r15) × 21, center z = 26 + 10.5 = 36.5
- Top: ⌀18 (r9) × 11, center z = 26 + 21 + 5.5 = 52.5
- Expected result: bbox 42 × 42 × 58, 3 cylindrical faces (r21, r15, r9), 4 planar faces, volume ≈ π·(21²·26 + 15²·21 + 9²·11) ≈ 53 665 mm³.