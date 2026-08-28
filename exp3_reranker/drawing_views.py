"""Extract per-view ink-bbox aspect ratios from the eval-cache drawing PNGs.

Drawings ink-code content: part geometry is black/gray (visible/hidden edges),
dimensions + labels + title block are blue. Filtering out blue leaves geometry-only
ink; coarse-grid connected components then give one blob per view. Layout is fixed:
Front bottom-left, Top above Front (shares X), Right beside Front (shares Z/height),
ISO far right (no dimensions). Ratios only — scale-invariant, so the title-block
scale note is irrelevant.

Per view v with ink bbox (w, h):  front w/h = X/Z,  top w/h = X/Y,  right w/h = Y/Z.
Also emits cross-view consistency (top.w vs front.w, right.h vs front.h) as an
extraction-quality signal.

    python drawing_views.py [--debug-keys k1,k2] -> drawing_views.json (committed)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import pickle

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = "/srv/scratch/bimrose2/drawing_agent_exp1/wds_dataset/eval_cache_v15.pkl"
CELL = 12          # coarse-grid cell (px)
MIN_CELLS = 12     # drop specks


def geometry_mask(a: np.ndarray) -> np.ndarray:
    """True where ink is part geometry (black/gray), not blue annotation."""
    r = a[..., 0].astype(np.int16)
    b = a[..., 2].astype(np.int16)
    dark = a.sum(axis=2) < 600          # not background white / light antialias
    not_blue = (b - r) < 25             # blue ink (dims/labels/title) excluded
    return dark & not_blue


def coarse_components(mask: np.ndarray):
    """Union-find on occupied CELLxCELL cells, 8-connected with 1-cell tolerance
    (bridges dashed lines and small intra-view gaps)."""
    H, W = mask.shape
    gh, gw = H // CELL + 1, W // CELL + 1
    occ = np.zeros((gh, gw), bool)
    ys, xs = np.nonzero(mask)
    occ[ys // CELL, xs // CELL] = True
    # dilate by 1 cell
    d = occ.copy()
    d[1:, :] |= occ[:-1, :]; d[:-1, :] |= occ[1:, :]
    d[:, 1:] |= occ[:, :-1]; d[:, :-1] |= occ[:, 1:]
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    cells = list(zip(*np.nonzero(d)))
    for c in cells:
        parent[c] = c
    cs = set(cells)
    for (i, j) in cells:
        for di, dj in ((0, 1), (1, 0), (1, 1), (1, -1)):
            n = (i + di, j + dj)
            if n in cs:
                union((i, j), n)
    groups = {}
    for c in cells:
        if occ[c]:  # only original cells define bboxes
            groups.setdefault(find(c), []).append(c)
    blobs = []
    for cells_ in groups.values():
        if len(cells_) < MIN_CELLS:
            continue
        # tight pixel bbox from the mask inside the cell region
        ii = [c[0] for c in cells_]; jj = [c[1] for c in cells_]
        y0, y1 = min(ii) * CELL, (max(ii) + 1) * CELL
        x0, x1 = min(jj) * CELL, (max(jj) + 1) * CELL
        sub = mask[max(0, y0 - CELL):y1 + CELL, max(0, x0 - CELL):x1 + CELL]
        sy, sx = np.nonzero(sub)
        if len(sy) < 40:
            continue
        oy, ox = max(0, y0 - CELL), max(0, x0 - CELL)
        blobs.append({"x0": int(ox + sx.min()), "x1": int(ox + sx.max()),
                      "y0": int(oy + sy.min()), "y1": int(oy + sy.max()),
                      "n_px": int(len(sy))})
    return blobs


def assign_views(blobs, W, H, tol=30):
    """Orthographic alignment: front & right share the vertical span (both drawn to
    the same Z scale, same baseline); front & top share the horizontal span (same X).
    front = the blob with a y-span-aligned blob to its right and/or an x-span-aligned
    blob above it; iso = largest unassigned far-right blob."""
    blobs = [bl for bl in blobs if bl["n_px"] >= 800]   # drop text specks
    if not blobs:
        return {}
    for bl in blobs:
        bl["cx"] = (bl["x0"] + bl["x1"]) / 2
        bl["cy"] = (bl["y0"] + bl["y1"]) / 2

    def y_aligned(a, b):
        return abs(a["y0"] - b["y0"]) <= tol and abs(a["y1"] - b["y1"]) <= tol

    def x_aligned(a, b):
        return abs(a["x0"] - b["x0"]) <= tol and abs(a["x1"] - b["x1"]) <= tol

    best_f, best_score = None, -1
    for f in blobs:
        rights = [b for b in blobs if b is not f and b["cx"] > f["cx"] and y_aligned(f, b)]
        tops = [b for b in blobs if b is not f and b["cy"] < f["cy"] and x_aligned(f, b)]
        score = (1 if rights else 0) + (1 if tops else 0)
        # prefer lower-left blobs on ties
        key = (score, -f["cx"] / W - f["x0"] / W + f["cy"] / H)
        if best_f is None or key > best_key:  # noqa: F821
            best_f, best_key, best_score = f, key, score
    views = {}
    if best_score > 0:
        f = best_f
        views["front"] = f
        rights = [b for b in blobs if b is not f and b["cx"] > f["cx"] and y_aligned(f, b)]
        tops = [b for b in blobs if b is not f and b["cy"] < f["cy"] and x_aligned(f, b)]
        if rights:
            views["right"] = min(rights, key=lambda b: b["cx"])
        if tops:
            views["top"] = min(tops, key=lambda b: -b["cy"])   # nearest above
    else:
        # no alignment: single projected view; take the leftmost sizable blob
        views["front"] = min(blobs, key=lambda b: b["cx"])
    used = {id(v) for v in views.values()}
    iso_cand = [bl for bl in blobs if id(bl) not in used and bl["cx"] > 0.55 * W]
    if iso_cand:
        views["iso"] = max(iso_cand, key=lambda bl: bl["n_px"])
    return views


def extract(png_bytes: bytes):
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    a = np.asarray(im)
    mask = geometry_mask(a)
    blobs = coarse_components(mask)
    views = assign_views(blobs, a.shape[1], a.shape[0])
    out = {"n_blobs": len(blobs), "views": {}}
    for name, bl in views.items():
        w = bl["x1"] - bl["x0"]; h = bl["y1"] - bl["y0"]
        out["views"][name] = {"w": w, "h": h,
                              "aspect": round(w / max(1, h), 4),
                              "bbox": [bl["x0"], bl["y0"], bl["x1"], bl["y1"]]}
    v = out["views"]
    if "front" in v and "top" in v:
        out["xw_consist"] = round(v["top"]["w"] / max(1, v["front"]["w"]), 3)
    if "front" in v and "right" in v:
        out["zh_consist"] = round(v["right"]["h"] / max(1, v["front"]["h"]), 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debug-keys", default=None)
    ap.add_argument("--debug-dir", default=None)
    args = ap.parse_args()
    with open(CACHE, "rb") as f:
        cache = pickle.load(f)
    samples = cache["samples"]
    out = {}
    n_full = 0
    for key, s in sorted(samples.items()):
        rec = extract(s["png"])
        out[key] = rec
        if all(n in rec["views"] for n in ("front", "top", "right")):
            n_full += 1
        if args.debug_keys and key[:8] in args.debug_keys:
            im = Image.open(io.BytesIO(s["png"])).convert("RGB")
            import PIL.ImageDraw
            dr = PIL.ImageDraw.Draw(im)
            for name, vv in rec["views"].items():
                dr.rectangle(vv["bbox"], outline=(255, 0, 0), width=3)
                dr.text((vv["bbox"][0], vv["bbox"][1] - 14), name, fill=(255, 0, 0))
            os.makedirs(args.debug_dir or ".", exist_ok=True)
            im.save(os.path.join(args.debug_dir or ".", f"dbg_{key[:8]}.png"))
    print(f"extracted front+top+right for {n_full}/{len(samples)} drawings")
    with open(os.path.join(HERE, "drawing_views.json"), "w") as f:
        json.dump(out, f, indent=0, sort_keys=True)
    print("wrote drawing_views.json")


if __name__ == "__main__":
    main()
