# 0eec11b2-ceda-f288-f912-84a01f311449 — agentic final (cand 3), IoU 0.889
from build123d import *

# ---- dimensions read from the drawing ----
L = 80            # mm  overall length, X (top & front views)
W = 50            # mm  overall width,  Y (right view)
H = 30            # mm  overall height, Z (front & right views)

hole_d = 5        # mm  4x Ø5 THRU (vertical holes)
hole_in = 8       # mm  hole-centre inset from each edge (the "8" dims)
hx1 = hole_in          # 8
hx2 = L - hole_in      # 72  (the "72" baseline dim = 80-8)
hy1 = hole_in          # 8
hy2 = W - hole_in      # 42  (the "42" baseline dim = 50-8)

# semicircular (half-round) scoop in the top, axis along X, centred in Y
groove_d = 42               # mm  scoop mouth width across Y (right view)
groove_r = groove_d / 2     # 21
groove_y = W / 2            # 25  -> mouth y = 4..46
groove_z = H                # axis on top face -> floor at H - groove_r = 9
groove_len = 20             # mm  compact central scoop along X (undimensioned on sheet,
                            #     inferred from the narrow central feature in Front/Top views)
groove_x = L / 2            # 40  -> scoop x = 30..50 (clear of holes and all side faces)

cham = 1          # mm  C1 chamfer on the four vertical corner edges

with BuildPart() as bp:
    Box(L, W, H, align=(Align.MIN, Align.MIN, Align.MIN))

    # 4 through holes Ø5 (vertical, +Z), over-extended to guarantee THRU
    with Locations([(hx1, hy1, H / 2), (hx2, hy1, H / 2),
                    (hx1, hy2, H / 2), (hx2, hy2, H / 2)]):
        Cylinder(radius=hole_d / 2, height=H + 2,
                 align=(Align.CENTER, Align.CENTER, Align.CENTER),
                 mode=Mode.SUBTRACT)

    # compact half-round scoop (R21) along X, centred in X and Y, opening at the top
    with Locations((groove_x, groove_y, groove_z)):
        Cylinder(radius=groove_r, height=groove_len, rotation=(0, 90, 0),
                 align=(Align.CENTER, Align.CENTER, Align.CENTER),
                 mode=Mode.SUBTRACT)

    # C1 chamfers on the four vertical corner edges
    chamfer(bp.part.edges().filter_by(Axis.Z), length=cham)

part = bp.part
export_step(part, "output.step")
