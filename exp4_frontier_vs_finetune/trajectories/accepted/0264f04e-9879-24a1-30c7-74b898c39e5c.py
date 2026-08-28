# 0264f04e-9879-24a1-30c7-74b898c39e5c — agentic final (cand 1), IoU 0.985
from build123d import *

# --- dimensions read from the drawing ---
flange_dia = 60.0      # mm  base flange diameter  (front view "Ø60")
flange_h   = 15.0      # mm  base flange thickness (front view chain)
boss_dia   = 40.0      # mm  middle boss diameter  (front view "Ø40")
boss_h     = 15.0      # mm  middle boss height    (front view chain)
top_dia    = 24.0      # mm  top boss diameter     (front view "Ø24")
top_h      = 20.0      # mm  top boss height       (front view chain)
hole_dia   = 5.0       # mm  through-hole diameter ("2× ⌀5 THRU")
hole_from_edge = 10.0  # mm  near hole centre from flange edge (right view "10";
                       #     far hole at "50" from the same edge)

# --- derived values ---
flange_r = flange_dia / 2                  # 30 mm (matches top view "30" edge-to-centre)
hole_off = flange_r - hole_from_edge       # 30 - 10 = 20 mm from axis (far hole: 30 + 20 = 50 ✓)
total_h  = flange_h + boss_h + top_h       # 15 + 15 + 20 = 50 mm

with BuildPart() as bp:
    # base flange Ø60 x 15
    Cylinder(radius=flange_r, height=flange_h,
             align=(Align.CENTER, Align.CENTER, Align.MIN))
    # middle boss Ø40 x 15
    with Locations((0, 0, flange_h)):
        Cylinder(radius=boss_dia / 2, height=boss_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # top boss Ø24 x 20
    with Locations((0, 0, flange_h + boss_h)):
        Cylinder(radius=top_dia / 2, height=top_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    # 2x Ø5 through holes on the Y axis at (0, ±20)
    with Locations((0, hole_off, 0), (0, -hole_off, 0)):
        Cylinder(radius=hole_dia / 2, height=total_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
