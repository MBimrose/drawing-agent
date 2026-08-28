# 10dff308-8a8d-b5da-769b-31f83512b5b7 — agentic final (cand 1), IoU 0.864
from build123d import *

# ---- dimensions read from the drawing ----
L = 70                  # mm  overall width X (top view, overall dim)
W = 50                  # mm  overall depth Y (right side view)
H_base = 20             # mm  base block height (front view, lowest level)
H_mid = 30              # mm  level: top of the short pins (front view)
H_top = 35              # mm  level: top of the tall pins = overall height (front view)
C2 = 2                  # mm  45 deg chamfer leg on the 4 vertical base corners (C2)

pin = 2                 # mm  square pin cross-section (repeated "2" callouts, top view)
pin_h_short = H_mid - H_base        # mm = 10
pin_h_tall = H_top - H_base         # mm = 15
pin_xs = [10, 25, 40, 55]           # mm  pin columns, ordinate from left edge (top view)
pin_ys = [10, 25, 40]               # mm  pin rows: 10 edge + 15 pitch inside W=50

hole_d = 6                # mm  blind-hole diameter (Ø6)
hole_depth = 4            # mm  blind-hole depth (↓4): 3 off front + 3 off back
hole_z = H_base / 2       # mm  hole axis height = 10 (centred in the 20 mm face)
hole_pitch = 20           # mm  "2x 20" spacing of the three holes
hole_xs = [L / 2 - hole_pitch, L / 2, L / 2 + hole_pitch]  # mm = 15, 35, 55 (centred)
overcut = 1               # mm  extra length so each blind hole opens cleanly at the face

x0, x1 = min(pin_xs), max(pin_xs)
y0, y1 = min(pin_ys), max(pin_ys)

with BuildPart() as bp:
    # base block, front-left-bottom corner at the origin
    Box(L, W, H_base, align=(Align.MIN, Align.MIN, Align.MIN))
    # C2 on the four vertical corner edges
    chamfer(bp.part.edges().filter_by(Axis.Z), length=C2)

    # square pins standing on the top face (z = H_base); grid corners are the tall pins
    for x in pin_xs:
        for y in pin_ys:
            h = pin_h_tall if (x in (x0, x1) and y in (y0, y1)) else pin_h_short
            with Locations((x, y, H_base)):
                Box(pin, pin, h, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # 3x Ø6 ↓4 on the front face (y=0, axis +Y) and 3x on the back face (y=W, axis -Y)
    front_c = (hole_depth - overcut) / 2   # cylinder centre -> spans y=-overcut .. hole_depth
    back_c = W - front_c                   # spans y=W-hole_depth .. W+overcut
    cyl_len = hole_depth + overcut
    centres = [(x, front_c, hole_z) for x in hole_xs] + \
              [(x, back_c, hole_z) for x in hole_xs]
    with Locations(*centres):
        Cylinder(radius=hole_d / 2, height=cyl_len,
                 align=(Align.CENTER, Align.CENTER, Align.CENTER),
                 rotation=(90, 0, 0), mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
