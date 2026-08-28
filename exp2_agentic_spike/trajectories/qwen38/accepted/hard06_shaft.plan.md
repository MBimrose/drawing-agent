# hard06_shaft — accepted trajectory plan

Reading the views:
- **Top view**: three concentric circles, labeled ⌀42 (outer), ⌀30 (middle), ⌀18 (inner). These are the diameters of the three coaxial cylindrical steps (the ISO view confirms a solid stepped cylinder — no internal hole, no hidden lines in any view).
- **Front view**: three stacked rectangles (silhouette of the steps) with vertical dimension chain: 11 (top step) + 21 (middle step) + 26 (bottom step) = 58 mm overall height.
- **Right view**: identical stacked-rectangle silhouette with the same chain 11 + 21 + 26 = 58 mm, confirming the part is a stack of three coaxial cylinders.
- **ISO view**: confirms overall form — large base cylinder, medium middle cylinder, small top cylinder, all solid.

Dimension chains:
- X/Y extents (from Top): 42, 30, 18 mm diameters.
- Z extent (Front/Right): 26 + 21 + 11 = 58 mm overall.

Feature list:
1. Bottom cylinder: ⌀42 × 26 high, base at Z=0.
2. Middle cylinder: ⌀30 × 21 high, from Z=26 to Z=47.
3. Top cylinder: ⌀18 × 11 high, from Z=47 to Z=58.
No holes, fillets, or chamfers are dimensioned.

---

Reading the views (unchanged from before — only the code binding was wrong):
- **Top view**: three concentric circles, ⌀42 (outer), ⌀30 (middle), ⌀18 (inner) → the three coaxial cylinder diameters.
- **Front view**: stacked rectangles, vertical chain 11 + 21 + 26 = 58 mm overall height.
- **Right view**: same silhouette, same chain 11 + 21 + 26 = 58 mm → confirms a solid 3-step coaxial cylinder (no holes, no hidden lines).
- **ISO view**: confirms overall stepped-cylinder form.

Dimension chains:
- X/Y (Top): 42, 30, 18 mm.
- Z (Front/Right): 26 + 21 + 11 = 58 mm.

Features:
1. Bottom cylinder ⌀42 × 26, base Z=0.
2. Middle cylinder ⌀30 × 21, base Z=26.
3. Top cylinder ⌀18 × 11, base Z=47.

Fix: in build123d 0.10 the `with BuildPart() as ...` object is the *context*, not the solid; the finished solid is `.part`. I also avoid method chaining on constructors (which can drop the object from the context) by positioning each cylinder with `pos` + `align` instead of `.translate`.

---

Reading the views (unchanged):
- **Top view**: three concentric circles ⌀42 / ⌀30 / ⌀18 → the three coaxial cylinder diameters.
- **Front view**: stacked rectangles, vertical chain 11 + 21 + 26 = 58 mm overall height.
- **Right view**: same silhouette, same chain 11 + 21 + 26 = 58 mm → solid 3-step coaxial cylinder (no holes, no hidden lines).
- **ISO view**: confirms the stepped-cylinder form.

Dimension chains:
- X/Y (Top): 42, 30, 18 mm.
- Z (Front/Right): 26 + 21 + 11 = 58 mm.

Features:
1. Bottom cylinder ⌀42 × 26, base Z=0.
2. Middle cylinder ⌀30 × 21, base Z=26.
3. Top cylinder ⌀18 × 11, base Z=47.

Fixes for build123d 0.10:
- `Cylinder` has no `pos` keyword → position each step with a `Locations((0,0,z))` context (the documented placement mechanism). A default `Cylinder(r,h)` already sits base-on-XY centered in XY, so only the Z translation is needed.
- Bind the finished solid via `part = bp.part` (the context object itself is not a shape).

---

Diagnosis of the mismatch (my reading of the drawing is unchanged):
- Original: 3 coaxial cylinders, ⌀42/⌀30/⌀18, heights 26/21/11, stacked face-to-face → overall Z = 26+21+11 = **58 mm**, single fused solid.
- My produced solid: Z = **65.5 mm**, **3 separate solids**, with visible gaps between the steps in the Front/Right renders.

Root cause: in build123d 0.10 the default `align` for `Cylinder` is `CENTER` on all axes, so each cylinder was centered on its `Locations` point instead of sitting base-on-top-of-the-previous one. That (a) shifted the whole stack (bottom spanned −13…+13, etc., giving 65.5 mm) and (b) left 2.5 mm gaps, so the union stayed 3 disjoint solids.

Fix: set `align=(Align.CENTER, Align.CENTER, Align.MIN)` on every cylinder so its base (min‑Z face) coincides with the `Locations` Z. Then:
- bottom: Z 0…26
- middle: Z 26…47
- top: Z 47…58  → overall Z = 58 mm, faces coincide → single fused solid.
Expected volume ≈ π(21²·26 + 15²·21 + 9²·11) ≈ 53 666 mm³.