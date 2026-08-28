# 0e14533a-a751-9f25-2cd8-9e95126e2806 — agentic final (cand 2), IoU 0.960
from build123d import *
import math

# --- Dimensions read from the drawing ---
W = 80.0             # mm  overall width (X), top & front views
D = 50.0             # mm  overall depth (Y), right view
H = 60.0             # mm  overall height (Z), front view
hole_d = 16.0        # mm  hole diameter (⌀16)
hole_depth = 30.0    # mm  hole depth from top face (↓30, blind)
dove_w = 24.0        # mm  dovetail opening width (⌀24)
dove_ang = 29.9      # deg dovetail wall angle from hole axis
slot_r = 3.0         # mm  2× R3 fillets on dovetail top edges
c_bot = 2.0          # mm  C2 chamfers on bottom edges
cx = 40.0            # mm  slot/hole center in X (dim 40)
cy = 25.0            # mm  hole center in Y (dim 25)

# derived: depth at which the 24-wide dovetail narrows to ⌀16
dove_depth = (dove_w - hole_d) / 2 / math.tan(math.radians(dove_ang))  # ≈ 6.96 mm

with BuildPart() as bp:
    # base block
    Box(W, D, H, align=(Align.MIN, Align.MIN, Align.MIN))

    # dovetail slot across the top, running the full depth in Y
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline([
                (cx - dove_w / 2, H),
                (cx - hole_d / 2, H - dove_depth),
                (cx + hole_d / 2, H - dove_depth),
                (cx + dove_w / 2, H),
            ], close=True)
        make_face()
    extrude(amount=D, both=True, mode=Mode.SUBTRACT)

    # ⌀16 blind hole, 30 mm deep from the top face
    with Locations((cx, cy, H)):
        Cylinder(radius=hole_d / 2, height=hole_depth,
                 align=(Align.CENTER, Align.CENTER, Align.MAX),
                 mode=Mode.SUBTRACT)

    # 2× R3 fillets on the two top edges of the dovetail slot
    slot_top_edges = (
        bp.edges()
        .filter_by(Axis.Y)
        .filter_by(lambda e: abs(e.center().Z - H) < 1e-3
                   and abs(abs(e.center().X - cx) - dove_w / 2) < 1e-3)
    )
    fillet(slot_top_edges, radius=slot_r)

    # C2 chamfers on the four bottom perimeter edges
    bottom_edges = bp.edges().filter_by(lambda e: abs(e.center().Z) < 1e-3)
    chamfer(bottom_edges, length=c_bot)

# bind the finished solid (not the builder) to `part`
part = bp.part

export_step(part, "output.step")
