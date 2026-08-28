# 0d6ee184-71db-63ad-e8f1-8f9ace368b67 — agentic final (cand 1), IoU 0.978
from build123d import *

# ---- parameters (all mm, read from the drawing) ----
W_total      = 70            # mm  overall width (X) - top & front views
D_total      = 42            # mm  overall depth (Y) - right view
T            = 10            # mm  plate thickness (Z) - front/right views
step_w       = 50            # mm  width of narrower rear portion - top view
front_hole_y = 15            # mm  front edge to front hole row - right view
rear_hole_y  = 36            # mm  front edge to rear hole (=15+21) - right view
hole_x_left  = 20            # mm  left hole X (baseline from left edge) - top view
hole_x_mid   = 35            # mm  middle hole X (= W_total/2) - top view
hole_x_right = 50            # mm  right hole X (= W_total-20) - top view
hole_d       = 5             # mm  3x dia5 THRU
fillet_r     = 2             # mm  6x R2 on convex plan corners

# ---- derived values ----
side_step = (W_total - step_w) / 2     # mm  shoulder inset per side = 10
step_y    = 2 * front_hole_y           # mm  shoulder plane = 30 (front row centered in wide part)
wide_d    = step_y                     # mm  wide front portion depth = 30
narrow_d  = D_total - step_y           # mm  narrow rear portion depth = 12 (rear hole centered: 30+6=36)
hole_r    = hole_d / 2

x0, x1 = 0, W_total                    # 0, 70
xa, xb = side_step, W_total - side_step  # 10, 60  (shoulders)
y0, ys, y2 = 0, step_y, D_total        # 0, 30, 42
convex_corners = {(x0, y0), (x1, y0), (x1, ys), (xb, y2), (xa, y2), (x0, ys)}  # 6 convex corners

with BuildPart() as bp:
    # wide front portion: X[0,70], Y[0,30], Z[0,10]
    Box(W_total, wide_d, T, align=(Align.MIN, Align.MIN, Align.MIN))
    # narrow rear portion (centered in X): X[10,60], Y[30,42], Z[0,10]
    with Locations((xa, ys, 0)):
        Box(step_w, narrow_d, T, align=(Align.MIN, Align.MIN, Align.MIN))

    # 6x R2 : fillet only the six convex vertical edges (re-entrant shoulder edges stay sharp)
    vedges = edges().filter_by(Axis.Z)
    sel = [e for e in vedges
           if (int(round(e.center().X)), int(round(e.center().Y))) in convex_corners]
    fillet(sel, radius=fillet_r)

    # 3x dia5 through holes
    hole_pts = [(hole_x_left, front_hole_y),
                (hole_x_right, front_hole_y),
                (hole_x_mid, rear_hole_y)]
    with Locations(*[(x, y, T / 2) for (x, y) in hole_pts]):
        Cylinder(radius=hole_r, height=T + 4, mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
