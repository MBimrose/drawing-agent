# 07035802-864d-0091-4bf7-4e785faf1a4f — agentic final (cand 1), IoU 0.903
from build123d import *

# ---------------- dimensions read from the drawing ----------------
base_L = 80.0        # mm  overall length (X), top view
base_W = 60.0        # mm  overall depth (Y), right view
base_t = 5.0         # mm  base plate thickness, front view
total_H = 17.0       # mm  overall height, front view
frame_inset = 4.0    # mm  frame set in from each base edge, front & right views
pocket_L = 60.0      # mm  pocket size in X  ("42 x 60 x 12 DEEP")
pocket_W = 42.0      # mm  pocket size in Y
pocket_depth = 12.0  # mm  pocket depth (= frame height, down to base top)
hole_d = 4.0         # mm  "12x Ø4 THRU (3x4)"
pitch_x = 22.7       # mm  "3x 22.7" column spacing
pitch_y = 24.0       # mm  "2x 24" row spacing
c1 = 1.0             # mm  C1 chamfer on the four base corners

# ---------------- derived values ----------------
frame_H = total_H - base_t          # 12 mm
frame_L = base_L - 2 * frame_inset  # 72 mm
frame_W = base_W - 2 * frame_inset  # 52 mm
col_x = [-1.5 * pitch_x, -0.5 * pitch_x, 0.5 * pitch_x, 1.5 * pitch_x]  # ±34.05, ±11.35
row_y = [-pitch_y, 0.0, pitch_y]                                      # -24, 0, +24

with BuildPart() as bp:
    # base plate 80 x 60 x 5
    Box(base_L, base_W, base_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # raised frame 72 x 52 x 12 sitting on the base
    with Locations((0, 0, base_t)):
        Box(frame_L, frame_W, frame_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        # pocket 60 x 42, 12 deep (floor = top of base plate)
        Box(pocket_L, pocket_W, pocket_depth + 1.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)

    # 12x Ø4 through holes, 4 columns x 3 rows
    with Locations([(x, y, -1.0) for x in col_x for y in row_y]):
        Cylinder(radius=hole_d / 2, height=total_H + 2.0,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    # C1 chamfers on the four vertical corner edges of the base plate
    corner_edges = (bp.edges()
                      .filter_by(Axis.Z)
                      .filter_by(lambda e: abs(abs(e.center().X) - base_L / 2) < 0.01
                                 and abs(abs(e.center().Y) - base_W / 2) < 0.01))
    chamfer(corner_edges, length=c1)

part = bp.part
export_step(part, "output.step")
