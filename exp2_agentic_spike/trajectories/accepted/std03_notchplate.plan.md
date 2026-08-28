# std03_notchplate — accepted trajectory plan

**Views read:**
- **Top (XY):** Outer rectangle. X-axis chain: 22 + 30 + 49 = **101** overall (matches printed 101). Y overall = **54**. A rectangular notch opens on the front (−Y) edge: 30 wide (x = 22→52), 18 deep (dimension "18" between front edge and notch back wall). Callout "2X ⌀6 THRU" with two circles sitting near the back edge, symmetric about X center: hole centers ≈16 mm from each side edge (16 and 85, centered on 50.5) and ≈18 mm from the back edge (y = 54−18 = 36).
- **Front (XZ):** 101 × 14 rectangle (Z overall = **14**). Solid vertical lines at x = 22 and x = 52 confirm the notch is on the front face and passes through the full thickness; faint dashed line pairs near x ≈ 16 and x ≈ 85 are the hidden hole edges.
- **Right (YZ):** 54 × 14 rectangle with two hidden vertical lines at y ≈ 18 (notch back wall) and y ≈ 36 (hole axis) — confirms notch depth 18 and hole Y position 36 from front.
- **ISO:** Flat plate with a through-thickness rectangular notch on one long edge and two through holes — consistent.

**Feature list:**
1. Base plate: 101 (X) × 54 (Y) × 14 (Z).
2. Through notch at front edge: 30 × 18, x from 22 to 52, full Z.
3. 2× ⌀6 through holes (Z) at (16, 36) and (85, 36) from the front-left corner.

---

**Verification found one real defect.** Comparing measurements to the drawing:

- Extents 101 × 54 × 14 ✓ (chain 22+30+49 = 101; depth 54; thickness 14).
- Notch 30 × 18 at x = 22→52 on the front edge ✓ (Front render shows solid lines at 22 and 52; Right render shows hidden line at y = 18).
- Hole positions ✓ (Top circles at x ≈ 16 and 85, y = 36 from front; Right hidden rectangle at y ≈ 36).
- **Hole depth ✗.** The callout is "2X ⌀6 THRU", but the volume gives it away: expected through-hole volume = 101·54·14 − 30·18·14 − 2·(π·3²·14) = 68004.3 mm³, yet measured = 68401.2 mm³ — a difference of ≈397 mm³ ≈ one half-depth hole pair (2·π·3²·7 = 395.9). Also 12 planar faces instead of the expected 10: the two extra planar faces are the floors of blind holes. Cause: build123d's `Cylinder` defaults to `align=CENTER` in Z, so at z = 0 the cylinders spanned z = −7…+7 and only cut the lower half. The Front/Right renders confirm this — the hidden hole rectangles occupy only the lower half of the 14 mm strip instead of its full height.

**Fix:** give the cylinders `align=(Align.CENTER, Align.CENTER, Align.MIN)` with base at z = 0 and height = T, producing true through holes. All other geometry is unchanged.