# std06_shaft — accepted trajectory plan

Reading the views:
- Top view: three concentric circles — outer ⌀48 (base flange), middle ⌀24 (middle cylinder), inner ⌀14 (top cylinder). The part is axisymmetric, so no X/Y linear dimensions are needed; all features are centered.
- Right view: three stacked tiers. Dimension chain in Z: base height 17 + middle cylinder 29 + top cylinder 10 = 56, which matches the overall 56 dimension. Widths in the Right view scale to 48 / 24 / 14, consistent with the Top view circles.
- ISO view: confirms a three-tier cylindrical stack (large flange, medium cylinder, small top cylinder).

Feature list (all centered on the Z axis):
1. Base flange: cylinder ⌀48, height 17 (z 0–17).
2. Middle cylinder: ⌀24, height 29 (z 17–46).
3. Top cylinder: ⌀14, height 10 (z 46–56).

No other features (no fillets/chamfers dimensioned). Overall height check: 17 + 29 + 10 = 56 ✓.

---

Reading the views (unchanged):
- Top view: three concentric circles — outer ⌀48 (base flange), middle ⌀24 (middle cylinder), inner ⌀14 (top cylinder). Axisymmetric, all centered.
- Right view: three stacked tiers. Z chain: 17 + 29 + 10 = 56, matching the overall 56 dimension. Widths scale to 48 / 24 / 14.
- ISO view: confirms three-tier cylindrical stack.

Feature list (centered on Z axis):
1. Base flange: ⌀48 × 17 (z 0–17).
2. Middle cylinder: ⌀24 × 29 (z 17–46).
3. Top cylinder: ⌀14 × 10 (z 46–56).

Fix: build123d 0.10 uses the `Align` enum (values `MIN`, `CENTER`, `MAX`), not `AlignOrigin`. Replaced `AlignOrigin.CENTER` → `Align.CENTER` and `AlignOrigin.BOTTOM` → `Align.MIN`.

---

Reading the views (unchanged):
- Top view: three concentric circles — outer ⌀48 (base flange), middle ⌀24 (middle cylinder), inner ⌀14 (top cylinder). Axisymmetric, all centered.
- Right view: three stacked tiers. Z chain: 17 + 29 + 10 = 56, matching the overall 56 dimension. Widths scale to 48 / 24 / 14.
- ISO view: confirms three-tier cylindrical stack.

Feature list (centered on Z axis):
1. Base flange: ⌀48 × 17 (z 0–17).
2. Middle cylinder: ⌀24 × 29 (z 17–46).
3. Top cylinder: ⌀14 × 10 (z 46–56).

Fix: in build123d 0.10 the primitive objects (`Cylinder`, etc.) do not expose a `.locations()` method — positioning is done with the `Locations(...)` context manager (or the `pos` argument). I now wrap each stacked cylinder in a `Locations(0, 0, z)` block so its local origin (centered in XY, bottom at local z=0 via `align=(Align.CENTER, Align.MIN)`) is translated to the correct stack height.

---

Reading the views (unchanged):
- Top view: three concentric circles — outer ⌀48 (base flange), middle ⌀24 (middle cylinder), inner ⌀14 (top cylinder). Axisymmetric, all centered.
- Right view: three stacked tiers. Z chain: 17 + 29 + 10 = 56, matching the overall 56 dimension. Widths scale to 48 / 24 / 14.
- ISO view: confirms three-tier cylindrical stack.

Feature list (centered on Z axis):
1. Base flange: ⌀48 × 17 (z 0–17).
2. Middle cylinder: ⌀24 × 29 (z 17–46).
3. Top cylinder: ⌀14 × 10 (z 46–56).

Fix: `Locations(...)` rejected three positional ints in this build123d version. I drop `Locations` entirely and position each stacked cylinder with the primitive's own `pos=(x, y, z)` argument combined with `align=(Align.CENTER, Align.MIN)` (centered in XY, bottom face at the local origin, then translated to the stack height). This is the most robust form.

---

Reading the views (unchanged):
- Top view: three concentric circles — outer ⌀48 (base flange), middle ⌀24 (middle cylinder), inner ⌀14 (top cylinder). Axisymmetric, all centered on the Z axis.
- Right view: three stacked tiers. Z chain: 17 + 29 + 10 = 56, matching the overall 56 dimension. Widths scale to 48 / 24 / 14.
- ISO view: confirms three-tier cylindrical stack.

Feature list (concentric, stacked in Z):
1. Base flange: ⌀48 × 17 (z 0–17).
2. Middle cylinder: ⌀24 × 29 (z 17–46).
3. Top cylinder: ⌀14 × 10 (z 46–56).

Fix for this build123d 0.10 build:
- `Cylinder` has no `.locations()` method and no `pos=` keyword (both rejected earlier).
- `Locations(0, 0, z)` (three bare ints) is rejected — its `__init__` iterates over each argument expecting a *point* (tuple/Vec/list), so a single 3‑tuple must be passed: `Locations((0, 0, z))`.
- I drop the ambiguous `align=` and rely on the default `Cylinder` placement; because all three cylinders share the same default XY placement they remain concentric, and only the Z offset (via `Locations`) differs. The part's absolute origin is irrelevant, only orientation/stacking matters.

---

Reading the views (unchanged):
- Top view: three concentric circles — outer ⌀48 (base flange), middle ⌀24 (middle cylinder), inner ⌀14 (top cylinder). Axisymmetric, all centered on the Z axis.
- Right view: three stacked tiers. Z chain: 17 + 29 + 10 = 56, matching the overall 56 dimension. Widths scale to 48 / 24 / 14.
- ISO view: confirms three-tier cylindrical stack.

Feature list (concentric, stacked in Z):
1. Base flange: ⌀48 × 17 (z 0–17).
2. Middle cylinder: ⌀24 × 29 (z 17–46).
3. Top cylinder: ⌀14 × 10 (z 46–56).

Fix for this build123d 0.10 build (geometry now builds cleanly; only the export target was wrong):
- `export_step` requires a `Part`/`Shape`, not the `BuildPart` context manager. The finished solid is `part.part` (the error hint "<BuildPart>.part.wrapped" confirms this). So export `part.part`.
- For robustness I now pass the explicit 3‑tuple `align=(Align.CENTER, Align.CENTER, Align.MIN)` to every `Cylinder` (centered in X/Y, base at local z=0), so concentricity and stacking do not depend on defaults. Z offsets are applied with `Locations((0, 0, z))` (a single 3‑tuple, which this build accepts).