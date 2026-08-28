# 0dd6ca4c-ec3c-67a5-8742-017faa18c6b4 — agentic final (cand 2), IoU 0.926
from build123d import *
from math import radians, tan

# ---------- dimensions read from the drawing ----------
bottom_dia  = 30.0   # mm  base cylinder dia (⌀30 leader, top view)
bottom_h    = 13.5   # mm  base cylinder height (front view)
max_dia     = 50.0   # mm  max body dia = 2 x R25 (radius dim, top view)
top_dia     = 25.0   # mm  top face dia (25 dim over right view)
total_h     = 80.0   # mm  overall height (front view)
waist_h     = 48.0   # mm  height of max dia (undimensioned; from view proportion 0.6*80)
hole_dia    = 10.0   # mm  ⌀10 blind hole from bottom face
hole_depth  = 25.0   # mm  total hole depth (front-view 25 dim = 21.6 straight + c'sink)
csink_dia   = 16.0   # mm  countersink diameter (⌄ ⌀16)
csink_angle = 82.0   # deg countersink included angle (× 82°)

# derived: depth of the 82° countersink cone (~3.45 mm; 21.6 + 3.45 ≈ 25)
csink_depth = (csink_dia - hole_dia) / 2 / tan(radians(csink_angle / 2))

# revolved half-profiles (r, z) in the XZ plane
profile = [
    (0, 0),
    (bottom_dia / 2, 0),
    (bottom_dia / 2, bottom_h),
    (max_dia / 2, waist_h),
    (top_dia / 2, total_h),
    (0, total_h),
]
hole_profile = [
    (0, 0),
    (csink_dia / 2, 0),                    # ⌀16 opening at bottom face
    (hole_dia / 2, csink_depth),           # 82° countersink cone
    (hole_dia / 2, hole_depth),            # ⌀10 straight hole to z = 25
    (0, hole_depth),
]

with BuildPart() as bp:
    # body of revolution
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline(*profile, (0, 0))
        make_face()
    revolve(axis=Axis.Z)

    # ⌀10 blind hole + ⌀16 x 82° countersink as one revolved cut
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline(*hole_profile, (0, 0))
        make_face()
    revolve(axis=Axis.Z, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
