# 02042bd8-55db-513c-2dd6-5a84d5c6e200 — agentic final (cand 1), IoU 0.972
from build123d import *

# ---- named dimensions read from the drawing (mm) ----
L = 80        # mm  overall X (top & front views)
W = 60        # mm  overall Y/depth (right view)
H = 30        # mm  overall Z (front & right views)
t = 2         # mm  wall and floor thickness (repeated "2" callouts)

d12 = 12          # mm  "2x ⌀12 THRU" through the bottom floor
hole12_x1 = 10    # mm  first ⌀12 centre from -X edge
hole12_x2 = 70    # mm  second ⌀12 centre from -X edge (= L-10, symmetric)
hole12_y = W / 2  # mm  row centred in depth (=30)

boss_lx = 10      # mm  boss size in X (top view)
boss_ly = 4       # mm  boss size in Y (top view "4")
boss_h = 5        # mm  boss height (front view "5"), stands on inner floor
boss_x = 40       # mm  boss centre X (top view datum = L/2)
boss_y = W / 2    # mm  boss centre Y (centred =30)

d4 = 4            # mm  "2x ⌀4 THRU" through the +X end wall
hole4_y1 = 10     # mm  first ⌀4 centre from -Y edge (right view)
hole4_y2 = 50     # mm  second ⌀4 centre from -Y edge (= W-10, symmetric)
hole4_z = 5       # mm  ⌀4 centre height on the wall (clear of the floor)

c = 1             # mm  C1 chamfer (45°) on the four outer corners
tol = 1e-4

with BuildPart() as bp:
    # outer block, origin at the -X/-Y/-Z corner
    Box(L, W, H, align=(Align.MIN, Align.MIN, Align.MIN))

    # open-top cavity: inset t on all sides, floor t, open at z = H
    with Locations((t, t, t)):
        Box(L - 2 * t, W - 2 * t, H - t,
            align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.SUBTRACT)

    # rectangular boss standing on the inner floor (top of floor at z = t)
    with Locations((boss_x, boss_y, t)):
        Box(boss_lx, boss_ly, boss_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.ADD)

    # 2x ⌀12 through the bottom floor (axis along Z)
    for hx in (hole12_x1, hole12_x2):
        with Locations((hx, hole12_y, -1)):
            Cylinder(d12 / 2, t + 2,
                     align=(Align.CENTER, Align.CENTER, Align.MIN),
                     mode=Mode.SUBTRACT)

    # 2x ⌀4 through the +X end wall (axis along X); rotate cylinder Z-axis onto +X
    for hy in (hole4_y1, hole4_y2):
        with Locations(Pos(L - t - 1, hy, hole4_z) * Rot(0, 90, 0)):
            Cylinder(d4 / 2, t + 2,
                     align=(Align.CENTER, Align.CENTER, Align.MIN),
                     mode=Mode.SUBTRACT)

    # C1 chamfers on the four outer vertical corner edges only
    outer_vertical_edges = (
        bp.edges()
        .filter_by(Axis.Z)
        .filter_by(lambda e: (min(abs(e.center().X), abs(e.center().X - L)) < tol)
                             and (min(abs(e.center().Y), abs(e.center().Y - W)) < tol))
    )
    chamfer(outer_vertical_edges, c)

part = bp.part
export_step(part, "output.step")
