# std04_tblock — accepted trajectory plan

**View reading:**
- **Top (XY):** T-shaped outline. Overall X = 70 (given). Y axis is a chain: stem 35 + cross-bar 24 = 59, which matches the printed overall 59. The stem starts 28 from the left edge; the stem is drawn centered (Front view confirms symmetry), so stem width = 70 − 28 − 28 = 14.
- **Front (XZ):** Plain rectangle 70 × 17 with two visible vertical edges at x = 28 and x = 42 — the front edges of the narrow stem standing in front of the full-width cross-bar. Overall height Z = 17.
- **Right (YZ):** Plain rectangle 59 × 17 with one visible vertical edge at 35 from the front — the front face of the cross-bar. Chain check: 35 + 24 = 59. ✔
- **ISO:** Confirms a uniform-height (17 mm) T-shaped prism: full-width bar at the back, centered 14 mm stem running forward.

**Dimension chains:**
- X: 28 + 14 + 28 = 70 (overall given; stem width derived by symmetry)
- Y: 35 + 24 = 59 (overall given, matches)
- Z: 17 (overall given in Front and Right)

**Features:** single T-plan prism extruded 17 mm in Z; no holes, no fillets/chamfers.

---

Reading is unchanged (T-shaped prism: 70 × 59 × 17; cross-bar 24 deep at back, centered 14-wide stem 35 long in front). The failure was purely API usage: `Pos` cannot be used as a context manager in build123d 0.10 — replaced with `Locations(...)`, which shifts the local coordinate system inside `BuildPart`.

---

Reading is unchanged (T-shaped prism: 70 × 59 × 17; cross-bar 24 deep at back, centered 14-wide stem 35 long in front). The failure was a binding issue: `with BuildPart() as part:` binds the builder, not the solid — the finished solid must be extracted via `.part` before exporting.