# hard07_shaft — accepted trajectory plan

Reading the views:
- **Top view** (left, circles): three concentric circles giving the three cylinder diameters — outer ⌀42, middle ⌀22, inner ⌀16.
- **Front view** (left, below Top) and **Right view** (center): identical stepped elevations of three stacked rectangles. Vertical dimension chain (top→bottom): 13 + 18 + 26 = 57 mm total height. The rectangle widths match the three diameters (16 / 22 / 42).
- **ISO view** (top right): confirms three concentric solid cylinders stacked on the Z axis — large base, medium middle, small top. No through-hole is present (the "THRU" text is annotation noise; ISO shows solid bodies).

Dimension chain per axis:
- Z (height): 13 (top) + 18 (middle) + 26 (base) = **57 mm** overall.
- X & Y (diameters): base ⌀42, middle ⌀22, top ⌀16.

Feature list (concentric, on Z axis, base at Z=0):
1. Base cylinder: ⌀42 (R21), height 26, Z 0→26.
2. Middle cylinder: ⌀22 (R11), height 18, Z 26→44.
3. Top cylinder: ⌀16 (R8), height 13, Z 44→57.

No fillets/chamfers are dimensioned, so none added.

---

Reading unchanged from before — three concentric solid cylinders stacked on the Z axis:
- **Top view**: three concentric circles → diameters ⌀42 (base), ⌀22 (middle), ⌀16 (top).
- **Front / Right views**: identical stepped elevations; vertical chain 13 + 18 + 26 = **57 mm** total height; rectangle widths match the three diameters.
- **ISO view**: confirms three stacked solid cylinders (no through-hole).

Dimension chain per axis:
- Z (height): top 13 + middle 18 + base 26 = **57 mm**.
- X & Y: base ⌀42, middle ⌀22, top ⌀16.

Feature list (concentric, Z axis, base bottom at Z=0):
1. Base: R21, h26, Z 0→26
2. Middle: R11, h18, Z 26→44
3. Top: R8, h13, Z 44→57

Fix: build123d 0.10 uses `Align.MIN` (not `Align.MINIMUM`) for the bottom alignment.