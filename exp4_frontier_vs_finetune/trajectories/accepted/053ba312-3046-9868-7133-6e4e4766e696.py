# 053ba312-3046-9868-7133-6e4e4766e696 — agentic final (cand 1), IoU 0.926
from build123d import *

# ---- dimensions read from the drawing (mm) ----
D_outer = 80.0      # mm  outer diameter (front view)
D_inner = 70.0      # mm  through bore (front view leader)
H       = 60.0      # mm  overall height (front/right views)
R_half  = 40.0      # mm  right-view radius to centreline (= D_outer/2, check)

fin_root_dia = 73.0 # mm  diameter across opposite fin roots (plan)
fin_len      = 7.0  # mm  fin radial length (plan)
fin_t        = 4.0  # mm  fin tangential thickness (plan, two callouts)
seg_a        = 6.0  # mm  plan positional chain segment
seg_b        = 6.0  # mm  plan positional chain segment (seg_a + seg_b = 12, centred)

# ---- derived values ----
R_out  = D_outer / 2.0            # 40  (matches R_half)
R_in   = D_inner / 2.0            # 35
r_root = fin_root_dia / 2.0       # 36.5 (fin outer/root radius, inside the wall)
r_tip  = r_root - fin_len         # 29.5 (fin inner tip radius)
fin_angles = [0, 60, 120, 180, 240, 300]  # six fins, symmetry evident in plan/ISO

with BuildPart() as bp:
    # outer body, base on z=0, axis = Z
    Cylinder(radius=R_out, height=H,
             align=(Align.CENTER, Align.CENTER, Align.MIN))
    # through bore
    Cylinder(radius=R_in, height=H,
             align=(Align.CENTER, Align.CENTER, Align.MIN),
             mode=Mode.SUBTRACT)
    # six axial internal fins (radial plates, full height)
    for ang in fin_angles:
        with Locations(Rot(Z=ang) * Pos(r_tip, 0.0, 0.0)):
            Box(fin_len, fin_t, H,
                align=(Align.MIN, Align.CENTER, Align.MIN))

part = bp.part
export_step(part, "output.step")
