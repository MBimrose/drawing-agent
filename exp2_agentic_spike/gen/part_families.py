"""Parametric part families for exp2.

Each family function takes an rng and returns a dict:
  code      : GT build123d script text (named-parameter block, exports output.step)
  params    : {name: value_mm}
  suppress  : lengths (real mm) whose dimensions are HIDDEN in chained/indirect mode
              (the model must recover them by summing chain segments)
  required  : dimension label values (real mm) that MUST be placed on the sheet for
              the drawing to be solvable in the given mode (checked post-render)
  required_chained : extra values required in chained mode (the chain segments)
  family    : name

Distinctness: every displayed value is kept >=6% away from every suppressed value
(and chain segments pairwise distinct) so length-based suppression/dedup on
projected edges can't accidentally hide or merge a needed dimension.
"""
from __future__ import annotations

import random

MIN_SEP = 0.06  # 6% pairwise separation


def _distinct(values, sep=MIN_SEP):
    vals = [v for v in values if v is not None]
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            a, b = vals[i], vals[j]
            if abs(a - b) <= sep * max(a, b):
                return False
    return True


def _sample(rng, lo, hi, step=1):
    n = int((hi - lo) / step)
    return lo + step * rng.randint(0, n)


# ---------------------------------------------------------------------------

def steps3(rng):
    for _ in range(200):
        w1 = _sample(rng, 18, 34)
        w2 = _sample(rng, 20, 38)
        w3 = _sample(rng, 14, 30)
        h1 = _sample(rng, 8, 16)
        h2 = h1 + _sample(rng, 7, 15)
        h3 = h2 + _sample(rng, 8, 18)
        d = _sample(rng, 30, 55)
        W = w1 + w2 + w3
        r21, r32 = h2 - h1, h3 - h2
        # chain segments + other displayed values must be pairwise distinct and
        # away from the suppressed overalls (W, h3)
        if _distinct([w1, w2, w3, d, W]) and _distinct([h1, r21, r32, h2, h3]) \
           and _distinct([w1, w2, w3, h1, r21, r32, d]):
            break
    else:
        raise RuntimeError("steps3 sampling failed")
    params = dict(w1=w1, w2=w2, w3=w3, h1=h1, h2=h2, h3=h3, d=d)
    code = f"""from build123d import *

# ---- Named parameters (mm) ----
w1 = {w1:.1f}   # width of tallest (left) tier, along X
w2 = {w2:.1f}   # width of middle tier, along X
w3 = {w3:.1f}   # width of lowest (right) tier, along X
h1 = {h1:.1f}   # height of lowest tier, along Z
h2 = {h2:.1f}   # height of middle tier, along Z
h3 = {h3:.1f}   # height of tallest tier, along Z
d  = {d:.1f}   # depth, along Y

with BuildPart() as bp:
    Box(w1 + w2 + w3, d, h1, align=(Align.MIN, Align.MIN, Align.MIN))
    Box(w1 + w2, d, h2, align=(Align.MIN, Align.MIN, Align.MIN))
    Box(w1, d, h3, align=(Align.MIN, Align.MIN, Align.MIN))
part = bp.part
export_step(part, "output.step")
"""
    return dict(family="steps3", code=code, params=params,
                suppress=[float(W), float(h3)],
                required=[w1, w2, w3, h1, d],
                required_chained=[r21, r32],
                required_direct=[W, h3])


def notchplate(rng):
    for _ in range(200):
        W = _sample(rng, 70, 110)
        D = _sample(rng, 45, 70)
        T = _sample(rng, 8, 16)
        a = _sample(rng, 18, 32)
        nw = _sample(rng, 20, 36)
        nd = _sample(rng, 12, 25)
        b = W - a - nw
        dh = rng.choice([6, 8, 10])
        hx = _sample(rng, 12, 18)
        hy = _sample(rng, 12, 18)
        if b < 14:
            continue
        if _distinct([a, nw, b, D, T, nd, W]) and nd < D - 10:
            break
    else:
        raise RuntimeError("notchplate sampling failed")
    params = dict(W=W, D=D, T=T, a=a, nw=nw, nd=nd, dh=dh, hx=hx, hy=hy)
    code = f"""from build123d import *

# ---- Named parameters (mm) ----
W  = {W:.1f}   # overall plate width, along X
D  = {D:.1f}   # plate depth, along Y
T  = {T:.1f}   # plate thickness, along Z
a  = {a:.1f}   # left segment: notch offset from left edge, along X
nw = {nw:.1f}   # notch width, along X
nd = {nd:.1f}   # notch depth (cut into front edge), along Y
dh = {dh:.1f}   # hole diameter (2 holes)
hx = {hx:.1f}   # hole center inset from each side edge
hy = {hy:.1f}   # hole center inset from rear edge

with BuildPart() as bp:
    Box(W, D, T, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((a + nw / 2, nd / 2, T / 2)):
        Box(nw, nd, T, mode=Mode.SUBTRACT)
    with Locations((hx, D - hy, T / 2), (W - hx, D - hy, T / 2)):
        Cylinder(radius=dh / 2, height=T * 3, mode=Mode.SUBTRACT)
part = bp.part
export_step(part, "output.step")
"""
    return dict(family="notchplate", code=code, params=params,
                suppress=[float(W)],
                required=[a, nw, D, T, nd],
                required_chained=[b],
                required_direct=[W])


def lbracket(rng):
    for _ in range(200):
        A = _sample(rng, 55, 90)
        B = _sample(rng, 40, 70)
        t = _sample(rng, 9, 16)
        d = _sample(rng, 30, 55)
        dh = rng.choice([7, 9, 11])
        hx = _sample(rng, 12, 20)
        if _distinct([A - t, t, d, A]) and _distinct([B - t, t, B]) \
           and _distinct([A - t, B - t, t, d]):
            break
    else:
        raise RuntimeError("lbracket sampling failed")
    params = dict(A=A, B=B, t=t, d=d, dh=dh, hx=hx)
    code = f"""from build123d import *

# ---- Named parameters (mm) ----
A  = {A:.1f}   # horizontal leg length, along X
B  = {B:.1f}   # vertical leg height, along Z
t  = {t:.1f}   # leg thickness (both legs)
d  = {d:.1f}   # bracket width, along Y
dh = {dh:.1f}   # hole diameter in horizontal leg
hx = {hx:.1f}   # hole center inset from the free end of the horizontal leg

with BuildPart() as bp:
    Box(A, d, t, align=(Align.MIN, Align.MIN, Align.MIN))
    Box(t, d, B, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((A - hx, d / 2, t / 2)):
        Cylinder(radius=dh / 2, height=t * 3, mode=Mode.SUBTRACT)
part = bp.part
export_step(part, "output.step")
"""
    return dict(family="lbracket", code=code, params=params,
                suppress=[float(A), float(B)],
                required=[t, d],
                required_chained=[A - t, B - t],
                required_direct=[A, B])


def tblock(rng):
    for _ in range(200):
        ws = _sample(rng, 20, 34)
        c = _sample(rng, 14, 28)      # each bar overhang
        wb = ws + 2 * c
        hb = _sample(rng, 16, 28)
        hs = _sample(rng, 24, 44)
        T = _sample(rng, 10, 18)
        if _distinct([ws, c, hb, hs, T, wb, hs + hb]):
            break
    else:
        raise RuntimeError("tblock sampling failed")
    params = dict(wb=wb, hb=hb, ws=ws, hs=hs, T=T, c=c)
    code = f"""from build123d import *

# ---- Named parameters (mm) ----
wb = {wb:.1f}   # top bar width, along X
hb = {hb:.1f}   # top bar height, along Y
ws = {ws:.1f}   # stem width, along X (stem centered under the bar)
hs = {hs:.1f}   # stem height, along Y
T  = {T:.1f}   # thickness, along Z

with BuildPart() as bp:
    with Locations((0, hs / 2 + hb / 2, 0)):
        Box(wb, hb, T)
    Box(ws, hs, T)
part = bp.part
export_step(part, "output.step")
"""
    return dict(family="tblock", code=code, params=params,
                suppress=[float(wb)],
                required=[ws, hb, hs, T],
                required_chained=[c],
                required_direct=[wb, hs + hb])


def shaft(rng):
    for _ in range(200):
        d1 = _sample(rng, 30, 48, 2)
        d2 = _sample(rng, 18, 30, 2)
        d3 = _sample(rng, 8, 16, 2)
        l1 = _sample(rng, 14, 26)
        l2 = _sample(rng, 18, 34)
        l3 = _sample(rng, 10, 22)
        L = l1 + l2 + l3
        if d1 > d2 + 4 and d2 > d3 + 4 and _distinct([l1, l2, l3, L]) \
           and _distinct([d1, d2, d3]) and _distinct([l1, l2, l3, d1, d2, d3]):
            break
    else:
        raise RuntimeError("shaft sampling failed")
    params = dict(d1=d1, d2=d2, d3=d3, l1=l1, l2=l2, l3=l3)
    code = f"""from build123d import *

# ---- Named parameters (mm) ----
d1 = {d1:.1f}   # diameter of bottom section
d2 = {d2:.1f}   # diameter of middle section
d3 = {d3:.1f}   # diameter of top section
l1 = {l1:.1f}   # length of bottom section, along Z
l2 = {l2:.1f}   # length of middle section, along Z
l3 = {l3:.1f}   # length of top section, along Z

with BuildPart() as bp:
    Cylinder(d1 / 2, l1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations((0, 0, l1)):
        Cylinder(d2 / 2, l2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations((0, 0, l1 + l2)):
        Cylinder(d3 / 2, l3, align=(Align.CENTER, Align.CENTER, Align.MIN))
part = bp.part
export_step(part, "output.step")
"""
    return dict(family="shaft", code=code, params=params,
                suppress=[float(L)],
                required=[l1, l2, l3],
                required_chained=[],
                required_direct=[L])


def uchannel(rng):
    for _ in range(200):
        t = _sample(rng, 8, 14)
        gap = _sample(rng, 22, 44)
        W = 2 * t + gap
        H = _sample(rng, 28, 48)
        L = _sample(rng, 50, 85)
        hw = H - t   # inner slot depth
        if _distinct([t, gap, L, W]) and _distinct([hw, t, H]) \
           and _distinct([t, gap, hw, L]):
            break
    else:
        raise RuntimeError("uchannel sampling failed")
    params = dict(W=W, H=H, t=t, L=L, gap=gap)
    code = f"""from build123d import *

# ---- Named parameters (mm) ----
W = {W:.1f}   # outer width, along X
H = {H:.1f}   # outer height, along Z
t = {t:.1f}   # wall/floor thickness
L = {L:.1f}   # channel length, along Y

with BuildPart() as bp:
    Box(W, L, H, align=(Align.MIN, Align.MIN, Align.MIN))
    with Locations((W / 2, L / 2, t + (H - t) / 2)):
        Box(W - 2 * t, L, H - t, mode=Mode.SUBTRACT)
part = bp.part
export_step(part, "output.step")
"""
    return dict(family="uchannel", code=code, params=params,
                suppress=[float(W), float(H)],
                required=[t, gap, L],
                required_chained=[hw],
                required_direct=[W, H])


def bossplate(rng):
    for _ in range(200):
        W = _sample(rng, 60, 95)
        D = _sample(rng, 45, 75)
        t1 = _sample(rng, 8, 15)
        w2 = _sample(rng, 26, 44)
        d2 = _sample(rng, 20, 36)
        t2 = _sample(rng, 10, 20)
        dh = rng.choice([8, 10, 12])
        if w2 < W - 16 and d2 < D - 16 and _distinct([W, D, t1, w2, d2, t2, t1 + t2]):
            break
    else:
        raise RuntimeError("bossplate sampling failed")
    params = dict(W=W, D=D, t1=t1, w2=w2, d2=d2, t2=t2, dh=dh)
    code = f"""from build123d import *

# ---- Named parameters (mm) ----
W  = {W:.1f}   # base plate width, along X
D  = {D:.1f}   # base plate depth, along Y
t1 = {t1:.1f}   # base plate thickness, along Z
w2 = {w2:.1f}   # boss width, along X (boss centered on the plate)
d2 = {d2:.1f}   # boss depth, along Y
t2 = {t2:.1f}   # boss height above the plate, along Z
dh = {dh:.1f}   # center hole diameter (through everything)

with BuildPart() as bp:
    Box(W, D, t1)
    with Locations((0, 0, t1 / 2 + t2 / 2)):
        Box(w2, d2, t2)
    Cylinder(radius=dh / 2, height=(t1 + t2) * 3, mode=Mode.SUBTRACT)
part = bp.part
export_step(part, "output.step")
"""
    return dict(family="bossplate", code=code, params=params,
                suppress=[float(t1 + t2)],
                required=[W, D, t1, t2, w2, d2],
                required_chained=[],
                required_direct=[t1 + t2])


FAMILIES = dict(steps3=steps3, notchplate=notchplate, lbracket=lbracket,
                tblock=tblock, shaft=shaft, uchannel=uchannel, bossplate=bossplate)

# Part rosters: 10 standard (direct dims incl. overalls) + 10 hard (chained,
# overalls suppressed). Fresh seeds; every instance independently sampled.
ROSTER = {
    "std": ["steps3", "steps3", "notchplate", "notchplate", "tblock",
            "shaft", "shaft", "lbracket", "uchannel", "bossplate"],
    "hard": ["steps3", "steps3", "notchplate", "notchplate", "tblock",
             "tblock", "shaft", "shaft", "lbracket", "uchannel"],
}


def make_part(split: str, idx: int, seed_tag: str = "exp2-fresh-2026"):
    fam_name = ROSTER[split][idx]
    rng = random.Random(f"{seed_tag}/{split}/{idx}/{fam_name}")
    spec = FAMILIES[fam_name](rng)
    spec["split"] = split
    spec["uid"] = f"{split}{idx:02d}_{fam_name}"
    return spec
