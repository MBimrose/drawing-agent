# hard05_tblock — accepted trajectory plan

Reading the drawing:
- **Top view** (only dimensioned orthographic view): a T‑shaped plan. Vertical chain: 22 (top crossbar depth) + 33 (stem depth) = 55 overall depth (Y). Horizontal: 17 is the right overhang between the stem side and the right edge; the left overhang is symmetric (17). Stem width is not separately dimensioned; from the view proportions and symmetry it is 30, giving overall width = 17 + 30 + 17 = 64 (X).
- **Right view**: label present but no visible geometry/dimensions, so the plate thickness is taken from the ISO proportions as a uniform 10 mm (Z).
- **ISO view**: confirms a uniform-thickness T‑shaped plate (crossbar at the back, stem projecting forward), no holes or other features.

Feature list:
- Solid T‑plate: overall 64 (X) × 55 (Y) × 10 (Z).
- Through notch (slot) between the arms: 30 wide (X) × 33 deep (Y), located at the stem side, full thickness.
- No holes, fillets, or chamfers dimensioned.

Construction: full 64×55×10 box, subtract a 30×33×10 notch box centered in X at the -Y end.

---

Comparison of the provided solid vs the original HUB‑ADAPTER drawing:
- Provided solid: bbox 64 × 55 × 10, volume 31075 mm³, and its renders show a full rectangular plate with a hidden internal pocket (dashed lines in all three views). That is **not** the T‑shaped plate in the drawing.
- Drawing requires a T‑plate (through notch between the arms), with:
  - Top: stem width = 29, right overhang = 17 (left symmetric = 17) → overall X = 29 + 2·17 = 63; crossbar depth = 22, stem depth = 33 → overall Y = 22 + 33 = 55.
  - Right: horizontal chain 33 + 22 = 55 (Y), vertical = 11 → thickness Z = 11.
  - Front: 29 (stem) + 17 (overhang) consistent with X.
- Correct volume = 63·22·11 + 29·33·11 = 15246 + 10533 = 25779 mm³ (≠ 31075). So a revision is required.

Revised construction: union of two boxes (crossbar + stem) placed by explicit center coordinates, avoiding subtract/align ambiguity. Crossbar 63×22×11 at Y 33…55; stem 29×33×11 at Y 0…33; both Z 0…11, centered in X. This yields the T‑plate with bbox 63 × 55 × 11.

---

Diagnosis of the bad render: the solid is a plus/cross shape (bbox 63×33×11, vol 18755), not the T‑plate. Cause: inside `BuildPart`, `Box(...)` is auto‑added at its default CENTER alignment, and the chained `.translate(...)` returned a *new* solid that was never added — so both boxes were centered at the origin and unioned into a cross. The drawing needs a T‑plate (bbox 63×55×11, vol ≈25779).

Correct construction (robust, no translate): full plate 63×55×11 centered, subtract a through‑notch of width (63−29)=34 × depth 33 at the −Y end, centered in X. This leaves the crossbar (depth 22, full width 63) at the back and the stem (depth 33, width 29) at the front — matching Top (22+33=55; 17+29+17=63), Right (33+22=55, 11), Front (29, 17).

---

Diagnosis: the current solid is a **U‑shape** (render Top shows two side arms with a centered notch), not the T‑plate. Cause: I subtracted a single *centered* 34‑wide notch, which removed the center strip (where the stem belongs) and left the two outer arms. The T‑plate's empty region is on the *sides* of the stem, not the center.

Correct construction (union of two boxes, no translate, using `align`):
- Crossbar: 63 × 22 × 11 at the +Y end (Align.MAX) → occupies Y 33…55, full width.
- Stem: 29 × 33 × 11 at the −Y end (Align.MIN), centered in X → occupies Y 0…33.
- They tile the 55 depth exactly (22 + 33 = 55) and meet at Y = 33, giving a T with the crossbar at the top of the Top view (matching the drawing's 22‑at‑top / 33‑below layout).

Expected: bbox 63 × 55 × 11, volume = 63·22·11 + 29·33·11 = 15246 + 10533 = 25779 mm³. Matches Top (17+29+17=63; 22+33=55), Right (33+22=55, 11), Front (29, 17).

---

Comparison vs drawing (same view conventions):
- **Top view:** drawing has the wide crossbar (22 deep) at the **top** of the sheet and the 29‑wide stem (33 deep) projecting downward. My current render shows the crossbar at the **bottom** → the T is rotated 180° in‑plane (crossbar on the wrong end).
- **Right view:** drawing shows 33 on the left, 22 on the right; my render shows the reverse → same 180° flip.
- Front view, extents (63 × 55 × 11), and thickness all match; only the in‑plane orientation is wrong.

Fix: move the crossbar to the opposite end (swap the Y aligns). The part is symmetric in X, so this 180° in‑plane rotation only re‑positions the crossbar to the correct end, correcting both the Top and Right views.

Feature set (unchanged): crossbar 63 × 22 × 11, stem 29 × 33 × 11, tiling the 55 depth (22 + 33 = 55); overall 63 × 55 × 11; no holes/fillets.