# 01f125ec-6a23-34bb-4690-90f202c96d13 — agentic final (cand 1), IoU 0.834
from build123d import *

# ---- named dimensions read from the drawing (mm) ----
X_total   = 80   # mm  overall X (top/front)
y1        = 30   # mm  right-arm height (side chain seg 1) -> notch starts at Y=30
y2        = 10   # mm  middle zone of left leg (side chain seg 2)
y3        = 30   # mm  upper zone of left leg (side chain seg 3)
Y_total   = y1 + y2 + y3   # mm = 30+10+30 = 70 overall Y (matches right-view 70)
T         = 8    # mm  plate thickness (front/right views)
leg_w     = 30   # mm  left-leg width in X (top "30" = front "30")

step_y    = y1                 # mm  top of right arm / bottom of corner notch (=30)
notch_w   = X_total - leg_w    # mm  notch width  = 80-30 = 50
notch_h   = Y_total - step_y   # mm  notch height = 70-30 = 40

hole_d    = 6    # mm  "2x Ø6 THRU"
hole_r    = hole_d / 2
holeA_x   = 15   # mm  dim "15" (left edge to hole A centre)
holeA_y   = step_y - 7.5   # mm = 22.5 (dim "7.5" below the step)
holeB_x   = leg_w          # mm = 30 (lower hole, in right arm)
holeB_y   = y1 / 2         # mm = 15 (mid of 30-high arm)

slot_x0   = 10   # mm  dim "10" (left edge to slot left side)
slot_w    = 15   # mm  slot width in X (X 10 -> 25)
slot_h    = 8    # mm  slot height in Y (top-view "8")
slot_y1   = y1 + y2        # mm = 40 (top of the 10-wide zone)
slot_y0   = slot_y1 - slot_h   # mm = 32

sc_r      = 8 / 2  # mm  edge scallops Ø8 -> R4 (the "8" callouts), through plate

with BuildPart() as bp:
    # base plate and the upper-right corner notch (makes the L)
    Box(X_total, Y_total, T, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((leg_w, step_y, 0)):
        Box(notch_w, notch_h, T,
            align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.SUBTRACT)

    # rectangular through-slot next to the inner corner
    with Locations((slot_x0, slot_y0, 0)):
        Box(slot_w, slot_h, T,
            align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.SUBTRACT)

    # 2x Ø6 through holes
    with Locations((holeA_x, holeA_y, 0), (holeB_x, holeB_y, 0)):
        Cylinder(radius=hole_r, height=T,
                 align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

    # semicircular edge scallops (Ø8), cylinder centred on each edge
    scallops = [
        (0,       15,       0),   # left edge, lower
        (0,       45,       0),   # left edge, upper
        (20,      0,        0),   # bottom edge
        (60,      0,        0),   # bottom edge
        (X_total, 15,       0),   # right edge (arm tip)
        (leg_w,   55,       0),   # inner vertical notch edge
        (55,      step_y,   0),   # inner horizontal notch edge
    ]
    with Locations(*scallops):
        Cylinder(radius=sc_r, height=T,
                 align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
