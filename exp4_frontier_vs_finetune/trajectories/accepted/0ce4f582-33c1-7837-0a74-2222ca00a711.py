# 0ce4f582-33c1-7837-0a74-2222ca00a711 — agentic final (cand 1), IoU 0.980
from build123d import *

# ---- Dimensions read from the drawing ----
D = 80.0              # mm  overall diameter (front view: ⌀80)
H = 20.0              # mm  overall height (front view: 20)
R = D / 2             # mm  outer radius (right view half-dimension 40 confirms)

hole_dia = 5.0        # mm  through-hole diameter (narrow hole in SECTION A-A)
cbore_dia = 8.5       # mm  counterbore diameter (callout: 2x ⌀8.5 ↓1.4)
cbore_depth = 1.4     # mm  counterbore depth from top face

dim_h1 = 29.6         # mm  left rim -> hole 1 centre (top view)
dim_h2 = 49.6         # mm  left rim -> hole 2 centre (top view)
hole1_x = -R + dim_h1   # = -10.4 mm
hole2_x = -R + dim_h2   # = +9.6 mm  (spacing = 49.6 - 29.6 = 20.0)

notch_w = 4.0         # mm  rim notch width, "4 A/F" (top view)
notch_depth = 2.0     # mm  rim notch depth (top view / SECTION A-A end steps)

with BuildPart() as bp:
    # main puck
    Cylinder(radius=R, height=H, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # two rim notches at the +/-X extremes, centred on Y=0, full height
    with Locations((R - notch_depth / 2, 0, H / 2),
                   (-(R - notch_depth / 2), 0, H / 2)):
        Box(notch_depth, notch_w, H, mode=Mode.SUBTRACT)

    # two counterbored holes on the X axis (Y = 0)
    with Locations((hole1_x, 0, 0), (hole2_x, 0, 0)):
        Cylinder(radius=hole_dia / 2, height=H,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)
        with Locations((0, 0, H - cbore_depth)):
            Cylinder(radius=cbore_dia / 2, height=cbore_depth,
                     align=(Align.CENTER, Align.CENTER, Align.MIN),
                     mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
