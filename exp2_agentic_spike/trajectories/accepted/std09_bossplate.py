# std09_bossplate — agentic final (cand 1), IoU 1.000
from build123d import *

# --- Dimensions read from the drawing ---
base_w = 95      # mm  overall base width  (X)  [Top, Front]
base_d = 50      # mm  overall base depth  (Y)  [Top, Right]
total_h = 31     # mm  overall part height (Z)  [Front, Right]
boss_h = 20      # mm  boss height above base   [Front, Right]
boss_w = 35      # mm  boss width  (X)          [Top, Front]
boss_d = 29      # mm  boss depth  (Y)          [Top, Right]
hole_d = 12      # mm  through-hole diameter    [Top: Ø12 THRU]

# --- Derived values ---
base_h = total_h - boss_h   # mm  base plate thickness = 31 - 20 = 11

with BuildPart() as bp:
    # Base plate: centered in X/Y, bottom face at Z = 0
    Box(base_w, base_d, base_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Boss: centered in X/Y, standing on top of the base
    with Locations((0, 0, base_h)):
        Box(boss_w, boss_d, boss_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Ø12 through-hole: centered, passing through boss and base
    Cylinder(radius=hole_d / 2, height=total_h,
             align=(Align.CENTER, Align.CENTER, Align.MIN),
             mode=Mode.SUBTRACT)

part = bp.part
export_step(part, "output.step")
