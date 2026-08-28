# 014e0c04-50a5-9b2b-5d15-048cc68be62e — agentic final (cand 1), IoU 0.875
from build123d import *

# ---- Parameters (all mm, read from the drawing) ----
plate_L  = 80            # mm  overall X (FRONT view)
plate_W  = 35            # mm  plate width in Y (RIGHT view)
plate_T  = 6             # mm  plate thickness (FRONT view)
total_H  = 9             # mm  total height to top of rib (FRONT view)
rib_H    = total_H - plate_T   # mm  rib height above plate = 9 - 6 = 3
rib_W    = 43 - 37       # mm  rib width in X (TOP chain) = 6, centred at 40 = 80/2
rib_L    = 70            # mm  rib length in Y = overall depth (RIGHT view)
hole_D   = 5             # mm  2x Ø5 THRU
edge_CL  = 15            # mm  hole centre from each plate end (TOP view)
cham     = 0.5           # mm  C0.5 on the four plate corners

hole_off = plate_L / 2 - edge_CL   # mm  hole centre from part centre = 40 - 15 = 25
cut_extra = 2            # mm  overtravel so the thru cut fully clears the plate

# ---- Base plate 80 x 35 x 6 (Z = 0..6), centred in XY ----
base = Box(plate_L, plate_W, plate_T,
           align=(Align.CENTER, Align.CENTER, Align.MIN))
# C0.5 chamfer on the four vertical corner edges of the plate only
base = chamfer(base.edges().filter_by(Axis.Z), cham)

# ---- Raised rib 6 (X) x 70 (Y) x 3, sitting on top of the plate (Z = 6..9) ----
rib = Box(rib_W, rib_L, rib_H,
          align=(Align.CENTER, Align.CENTER, Align.MIN)).move(Location((0, 0, plate_T)))

part = base + rib

# ---- 2x Ø5 through-holes at x = +/-25, y = 0 ----
for x in (-hole_off, hole_off):
    part -= Cylinder(hole_D / 2, plate_T + 2 * cut_extra,
                     align=(Align.CENTER, Align.CENTER, Align.MIN)
                     ).move(Location((x, 0, -cut_extra)))

export_step(part, "output.step")
