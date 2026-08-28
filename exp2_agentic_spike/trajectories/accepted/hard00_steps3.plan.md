# hard00_steps3 — accepted trajectory plan

Top view (XY): footprint is a rectangle. X is given only as a component chain: 28 + 21 + 17 = 66 mm overall. Y is an overall dimension = 36 mm. Two interior lines parallel to Y (at x = 28 and x = 28+21 = 49) are the step breaks.

Front view (XZ): a staircase profile, tall on the left stepping down to the right. The Z riser chain is 10 + 13 + 15 = 38 mm total. Each X segment is paired with a riser: the 28-wide segment carries the top riser (15) so it reaches 10+13+15 = 38; the 21-wide segment carries the 13 riser so it reaches 10+13 = 23; the 17-wide segment is the lowest tread at height 10. So solid height by X: [0,28]→38, [28,49]→23, [49,66]→10.

Right view (YZ, from +X): 36 (Y) × 38 (Z) with solid horizontal edges at z = 10 and z = 23. Seeing those edges as solid from +X confirms the low (10 mm) step is at the +X end and the taller steps rise behind it — consistent with the Front view (high at low X, low at high X).

Features: three rectangular treads, each spanning the full 36 mm Y depth. No hole callouts on this sheet; no dimensioned fillets/chamfers (omitted).

Build: fuse three boxes — base 66×36×10 (z 0–10, full footprint); middle 49×36×13 (z 10–23, over the high+mid steps); top 28×36×15 (z 23–38, over the high step only). This yields exactly the chained heights 10 / 23 / 38.