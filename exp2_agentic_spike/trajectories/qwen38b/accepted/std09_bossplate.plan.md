# std09_bossplate — accepted trajectory plan

Views: Top (XY, X right / Y up), Right (YZ, Y right / Z up), ISO (form only).

- Top view: outer rectangle = base plate; overall vertical (Y) dimension = 50. Inner rectangle = boss, vertical (Y) dimension = 20, centered on the plate. Circle callout "⌀12 THRU" centered in the boss.
- Right view: base plate below, boss above. Vertical dimensions: boss height = 20, overall height = 31. So plate thickness = 31 − 20 = 11 (chain: 11 + 20 = 31).
- X axis: no explicit dimension printed; from the Top view proportions (plate aspect ≈ 2:1, boss ≈ 0.4 of plate length) the plate length X = 100 and boss length X = 40, both centered.
- Feature list:
  1. Base plate 100 (X) × 50 (Y) × 11 (Z).
  2. Boss 40 (X) × 20 (Y) × 20 (Z), centered, sitting on the plate top (z = 11 to 31).
  3. ⌀12 through-hole, centered, through boss and plate (depth 31).
- No fillets/chamfers dimensioned → omit.

---

Reading unchanged from before; only the construction method needed fixing (a bare `Box` solid has no `.locations()` method in build123d 0.10 — use a nested `with Locations(...)` block to place the boss).

- Top view: base plate overall Y = 50; boss Y = 20 centered; ⌀12 THRU hole centered.
- Right view: overall height 31, boss height 20 → plate thickness = 31 − 20 = 11.
- X axis from Top-view proportions: plate X = 100, boss X = 40, both centered.
- Features: plate 100×50×11 (z 0→11); boss 40×20×20 centered (z 11→31); ⌀12 through-hole centered (depth 31). No fillets/chamfers.

---

Reading unchanged (Top: plate Y=50, boss Y=20 centered, ⌀12 THRU centered; Right: overall 31, boss 20 → plate 11; X from Top proportions: plate 100, boss 40 centered). The only fix is construction: in build123d 0.10 a `Box` has no `.locations()` method, and `Location(0,0,z)` (three positional floats) is an invalid constructor form. I place the boss with the standard `pos=Vector(...)` keyword on the `Box` primitive (a pure translation applied after `align`), which is robust and needs no `Location`/`Locations` at all.

- Plate 100×50×11, centered X/Y, z 0→11.
- Boss 40×20×20, centered X/Y, translated to z 11→31 via `pos=Vector(0,0,11)`.
- ⌀12 through-hole centered, z 0→31, subtracted.
- No fillets/chamfers.

---

Reading unchanged (Top: plate Y=50, boss Y=20 centered, ⌀12 THRU centered; Right: overall 31, boss 20 → plate 11; X from Top proportions: plate 100, boss 40 centered). The fix: in build123d 0.10 the `Location` constructor rejects three positional floats, but accepts a single `Vector` as a translation. So the boss is placed with `with Locations(Location(Vector(0, 0, plate_t))):` (the `Locations` context itself was fine — only the `Location` argument form was wrong).

- Plate 100×50×11, centered X/Y, z 0→11.
- Boss 40×20×20, centered X/Y, translated to z 11→31 via `Location(Vector(0,0,11))`.
- ⌀12 through-hole centered, z 0→31, subtracted.
- No fillets/chamfers.