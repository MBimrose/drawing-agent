# hard07_shaft — accepted trajectory plan

Reading the views:
- **Top view:** three concentric circles, labeled ⌀42 (outer), ⌀22 (middle), ⌀16 (inner). These are the outlines of three coaxial cylindrical steps. No hidden circles/holes are shown.
- **Right view:** three stacked rectangles (a stepped cylinder seen from the side). Height chain from the bottom: 26 (widest step) + 18 (middle step) + 13 (top step) = 57 mm overall height. Widths of the steps correspond to the diameters 42 / 22 / 16 (pixel ratios ≈ 1 : 0.55 : 0.38 match 42 : 22 : 16). No hidden lines → solid, no through holes.
- **ISO view:** confirms the form: large base disc, smaller middle cylinder, smallest top cylinder, all coaxial.

Dimension chains:
- X/Y extents: 42 (base), 22 (middle), 16 (top) — all diameters, coaxial.
- Z extent: 26 + 18 + 13 = 57 mm overall.

Feature list:
1. Base cylinder: ⌀42 × 26 high, z = 0…26.
2. Middle cylinder: ⌀22 × 18 high, z = 26…44.
3. Top cylinder: ⌀16 × 13 high, z = 44…57.
All solid, no holes, no fillets/chamfers dimensioned.

---

Reading the views (unchanged from before):
- **Top view:** three concentric circles ⌀42 (outer), ⌀22 (middle), ⌀16 (inner) → three coaxial cylindrical steps. No hidden circles → no holes.
- **Right view:** three stacked rectangles; height chain 26 + 18 + 13 = 57 mm overall. Step widths match diameters 42 / 22 / 16.
- **ISO view:** confirms stepped solid cylinder (large base disc, middle cylinder, small top cylinder), all coaxial, solid.

Dimension chains:
- X/Y: 42 / 22 / 16 (coaxial diameters).
- Z: 26 + 18 + 13 = 57 mm overall.

Feature list:
1. Base cylinder ⌀42 × 26, z = 0…26.
2. Middle cylinder ⌀22 × 18, z = 26…44.
3. Top cylinder ⌀16 × 13, z = 44…57.
Solid, no holes, no fillets/chamfers.

API fix: in build123d 0.10 the finished solid is exposed as `p.part` (not `p.obj()`). Bind `part = p.part` before export.