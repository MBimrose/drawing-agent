# 0cfc10be-e86a-0791-d268-d7edf63e84e9 — agentic final (cand 1), IoU 0.819
from build123d import *

# ---------------- dimensions read from the drawing ----------------
flange_dia    = 60.0   # mm  flange diameter (front view width / top view circle)
flange_h      = 20.0   # mm  flange height (front view)
overall_h     = 60.0   # mm  total height, flange bottom -> blade top (front view)
blade_thk     = 8.0    # mm  blade thickness in X (top view)
blade_len     = 40.0   # mm  blade length in Y (right view)
blade_tip_y   = 25.0   # mm  blade +Y edge measured from flange axis (top view)
edge_to_blade = 34.0   # mm  flange -X edge to blade +X face (top view)
hole_dia      = 6.0    # mm  central through hole (front view leader)
boss_dia      = 10.0   # mm  central boss diameter (front view leader)
boss_h        = 4.0    # mm  boss height above flange (scaled from 1:1 views; not directly dimensioned)

# ---------------- derived values ----------------
flange_r  = flange_dia / 2.0
blade_h   = overall_h - flange_h          # 40 mm of blade above the flange
blade_x_hi = edge_to_blade - flange_r     # +4 mm  blade +X face
blade_x_lo = blade_x_hi - blade_thk       # -4 mm  (blade centred on X)
blade_y_hi = blade_tip_y                  # +25 mm
blade_y_lo = blade_y_hi - blade_len       # -15 mm
blade_cx  = (blade_x_lo + blade_x_hi) / 2 # 0
blade_cy  = (blade_y_lo + blade_y_hi) / 2 # +5

# ---------------- solid ----------------
flange = Cylinder(radius=flange_r, height=flange_h,
                  align=(Align.CENTER, Align.CENTER, Align.MIN))

boss = Pos(0, 0, flange_h) * Cylinder(
    radius=boss_dia / 2, height=boss_h,
    align=(Align.CENTER, Align.CENTER, Align.MIN))

blade = Pos(blade_cx, blade_cy, flange_h) * Box(
    blade_thk, blade_len, blade_h,
    align=(Align.CENTER, Align.CENTER, Align.MIN))

# central through hole (flange + boss), axis at the origin
hole = Cylinder(radius=hole_dia / 2, height=flange_h + boss_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

part = flange + boss + blade - hole

export_step(part, "output.step")
