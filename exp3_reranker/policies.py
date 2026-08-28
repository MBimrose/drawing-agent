"""Selection policies for exp3. Selection-time inputs ONLY:
- shard exec_ok (which draws executed),
- re-executed candidate geometry features (features.json),
- drawing-view aspect ratios (drawing_views.json).
Never IoU, never GT.

Each policy: (rec, ctx) -> draw index or None (None = repair fallback).
"""
from __future__ import annotations

import json
import math
import os

import bo4data

HERE = os.path.dirname(os.path.abspath(__file__))


def load_ctx():
    feats = json.load(open(os.path.join(HERE, "features.json")))["features"]
    views = json.load(open(os.path.join(HERE, "drawing_views.json")))
    ctx = {"feats": feats, "views": views}
    pw = os.path.join(HERE, "pairwise_iou.json")
    if os.path.exists(pw):
        ctx["pairwise"] = json.load(open(pw))
    return ctx


# --- per-candidate feature helpers ------------------------------------------

def cand_feat(ctx, rec, draw_idx):
    return ctx["feats"].get(rec["draws"][draw_idx]["tag"], {})


def degenerate_flags(f: dict) -> list[str]:
    """Cheap absolute sanity checks on one candidate's geometry."""
    flags = []
    if not f.get("exec_ok"):
        return ["no_geom"]
    vol = f.get("volume_mm3", 0.0)
    if vol < 1.0:
        flags.append("tiny_volume")
    if f.get("fill_frac", 1.0) < 0.005:
        flags.append("sliver_fill")
    if f.get("aspect", 1.0) > 60:
        flags.append("extreme_aspect")
    if not f.get("watertight", True):
        flags.append("not_watertight")
    if f.get("n_solids", 1) > 3 or f.get("n_mesh_components", 1) > 3:
        flags.append("many_solids")
    return flags


def geo_dist(fa: dict, fb: dict) -> float:
    """Scale-free geometric disagreement between two candidates: max |log ratio|
    over sorted bbox extents and volume^(1/3)."""
    ea = sorted(fa.get("bbox_mm", [1e-6] * 3))
    eb = sorted(fb.get("bbox_mm", [1e-6] * 3))
    terms = []
    for a, b in zip(ea, eb):
        terms.append(abs(math.log(max(a, 1e-6) / max(b, 1e-6))))
    va = max(fa.get("volume_mm3", 1e-9), 1e-9) ** (1 / 3)
    vb = max(fb.get("volume_mm3", 1e-9), 1e-9) ** (1 / 3)
    terms.append(abs(math.log(va / vb)))
    return max(terms)


def consensus_scores(ctx, rec):
    """median geo-distance of each executing draw to the other executing draws.
    Returns {draw_idx: med_dist}; empty/1-draw cases get 0.0."""
    ex = [d["draw"] for d in bo4data.exec_draws(rec)]
    fs = {i: cand_feat(ctx, rec, i) for i in ex}
    out = {}
    for i in ex:
        ds = sorted(geo_dist(fs[i], fs[j]) for j in ex if j != i)
        if not ds:
            out[i] = 0.0
        else:
            mid = len(ds) // 2
            out[i] = ds[mid] if len(ds) % 2 else 0.5 * (ds[mid - 1] + ds[mid])
    return out


def aspect_mismatch(ctx, rec, draw_idx):
    """max |log(candidate view aspect / drawing view aspect)| over extracted views;
    None if unusable (missing views, inconsistent extraction, or missing bbox)."""
    dv = ctx["views"].get(rec["key"], {})
    vw = dv.get("views", {})
    f = cand_feat(ctx, rec, draw_idx)
    bb = f.get("bbox_mm")
    if not bb:
        return None
    X, Y, Z = [max(v, 1e-6) for v in bb]
    pred = {"front": X / Z, "top": X / Y, "right": Y / Z}
    # trust extraction only if the two cross-view scale checks (when present) hold
    for c in ("xw_consist", "zh_consist"):
        if c in dv and abs(dv[c] - 1.0) > 0.06:
            return None
    terms = []
    for name in ("front", "top", "right"):
        if name in vw:
            meas = vw[name]["aspect"]
            if meas <= 0:
                continue
            terms.append(abs(math.log(pred[name] / meas)))
    if len(terms) < 2:      # need at least 2 views to constrain the box
        return None
    return max(terms)


# --- policies ----------------------------------------------------------------

def shape_consensus_dists(ctx, rec):
    """1 - median pairwise candidate-vs-candidate centered IoU (GT-free shape-space
    consensus; sees internal-feature differences that bbox consensus is blind to).
    {} if no pairwise data for this sample."""
    pw = ctx.get("pairwise", {}).get(rec["key"])
    if not pw:
        return {}
    ex = [d["draw"] for d in bo4data.exec_draws(rec)]
    out = {}
    for i in ex:
        vals = []
        for j in ex:
            if i == j:
                continue
            v = pw.get(f"{min(i, j)}-{max(i, j)}")
            if v is not None:
                vals.append(1.0 - v)
        if vals:
            vals.sort()
            mid = len(vals) // 2
            out[i] = vals[mid] if len(vals) % 2 else 0.5 * (vals[mid - 1] + vals[mid])
    return out


def make_shape_combined_policy(w_shape=1.0, w_asp=1.0, margin=0.05):
    """Like make_combined_policy but consensus lives in shape space (pairwise mesh
    IoU) instead of bbox space. Falls back to bbox consensus when pairwise data is
    missing for a sample."""
    def pol(rec, ctx):
        ex = [d["draw"] for d in bo4data.exec_draws(rec)]
        if not ex:
            return None
        sh = shape_consensus_dists(ctx, rec)
        if not sh:
            sh = consensus_scores(ctx, rec)

        def score(i):
            s = w_shape * sh.get(i, 0.0)
            m = aspect_mismatch(ctx, rec, i)
            if m is not None:
                s += w_asp * m
            return s

        scored = {i: score(i) for i in ex}
        first = min(ex)
        best = min(ex, key=lambda i: (round(scored[i], 6), i))
        return best if scored[first] - scored[best] > margin else first
    return pol


def make_gated_policy(use_degenerate=True, use_consensus=True, use_aspect=True,
                      cons_tau=0.15, asp_tau=math.log(1.35)):
    """Deployed-compatible gate: keep first-exec unless flagged gross error; then
    fall through to the best unflagged candidate by (consensus, aspect, draw order).
    If everything is flagged, keep first-exec."""
    def pol(rec, ctx):
        ex = [d["draw"] for d in bo4data.exec_draws(rec)]
        if not ex:
            return None
        cons = consensus_scores(ctx, rec) if use_consensus else {i: 0.0 for i in ex}
        n_ex = len(ex)

        def flagged(i):
            if use_degenerate and degenerate_flags(cand_feat(ctx, rec, i)):
                return True
            # consensus outlier needs >=3 executing draws to be meaningful
            if use_consensus and n_ex >= 3 and cons[i] > cons_tau:
                return True
            if use_aspect:
                m = aspect_mismatch(ctx, rec, i)
                if m is not None and m > asp_tau:
                    return True
            return False

        first = min(ex)
        if not flagged(first):
            return first
        unflagged = [i for i in ex if not flagged(i)]
        if not unflagged:
            return first
        # among unflagged: lowest consensus dist, then lowest aspect mismatch, then order
        def rank(i):
            m = aspect_mismatch(ctx, rec, i) if use_aspect else None
            return (round(cons[i], 6), m if m is not None else 0.0, i)
        return min(unflagged, key=rank)
    return pol


def pol_consensus_medoid(rec, ctx):
    """Always pick the candidate most in agreement with the others (medoid);
    tie/degenerate-free preference by draw order."""
    ex = [d["draw"] for d in bo4data.exec_draws(rec)]
    if not ex:
        return None
    if len(ex) < 3:
        return min(ex)
    cons = consensus_scores(ctx, rec)
    return min(ex, key=lambda i: (round(cons[i], 6), i))


def pol_aspect_best(rec, ctx):
    """Always pick the candidate whose bbox ratios best match the drawing views."""
    ex = [d["draw"] for d in bo4data.exec_draws(rec)]
    if not ex:
        return None
    scored = [(aspect_mismatch(ctx, rec, i), i) for i in ex]
    usable = [(m, i) for m, i in scored if m is not None]
    if not usable:
        return min(ex)
    return min(usable, key=lambda t: (round(t[0], 6), t[1]))[1]


def make_combined_policy(w_cons=1.0, w_asp=1.0, margin=0.05):
    """Score every executing candidate: w_cons*consensus_med_dist + w_asp*aspect
    mismatch (when usable). Switch away from first-exec only when the best-scored
    candidate beats the first-exec score by > margin (protects good deployed picks)."""
    def pol(rec, ctx):
        ex = [d["draw"] for d in bo4data.exec_draws(rec)]
        if not ex:
            return None
        cons = consensus_scores(ctx, rec)

        def score(i):
            s = w_cons * cons[i]
            m = aspect_mismatch(ctx, rec, i)
            if m is not None:
                s += w_asp * m
            return s

        scored = {i: score(i) for i in ex}
        first = min(ex)
        best = min(ex, key=lambda i: (round(scored[i], 6), i))
        return best if scored[first] - scored[best] > margin else first
    return pol


def pol_degen_only(rec, ctx):
    """First-exec unless it is degenerate; then next non-degenerate by draw order."""
    ex = [d["draw"] for d in bo4data.exec_draws(rec)]
    if not ex:
        return None
    ok = [i for i in ex if not degenerate_flags(cand_feat(ctx, rec, i))]
    return min(ok) if ok else min(ex)
