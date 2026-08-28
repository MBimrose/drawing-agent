"""Exp 1 analysis: three-policy comparison from bo4_oracle JSON(s) (CPU, stdlib).

    python3 analyze_bo4.py <bo4_oracle.json | bo4_oracle_w*.json ...> [--md draft.md]

Accepts one merged JSON or many per-worker shard JSONs (records concatenated;
duplicate keys and partial dumps rejected). Computes deployed / oracle / greedy
means, paired gaps with bootstrap 95% CIs, which-draw-wins histograms, and a
per-sample table; optionally writes a RESULTS.md draft.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter


def policies(rec: dict) -> dict:
    draws = sorted(rec["draws"], key=lambda d: d["draw"])
    execd = [d for d in draws if d["exec_ok"]]
    rep = rec.get("repair")
    rep_iou = rep["iou_centered"] if rep and rep.get("exec_ok") else 0.0
    if execd:
        first = min(execd, key=lambda d: d["draw"])
        deployed, deployed_by = first["iou_centered"], first["draw"]
        best = max(execd, key=lambda d: d["iou_centered"])
        oracle, oracle_draw = best["iou_centered"], best["draw"]
    else:
        deployed = oracle = rep_iou
        deployed_by = oracle_draw = "repair" if rep_iou else None
    d0 = next((d for d in draws if d["draw"] == 0), None)
    greedy = d0["iou_centered"] if d0 and d0["exec_ok"] else 0.0
    return {"deployed": deployed, "deployed_by": deployed_by,
            "oracle": oracle, "oracle_draw": oracle_draw, "greedy": greedy,
            "n_exec": len(execd),
            "draw_ious": {d["draw"]: (d["iou_centered"] if d["exec_ok"] else None)
                          for d in draws}}


def boot_ci(diffs: list[float], iters: int = 20000, seed: int = 0):
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(iters))
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_paths", nargs="+")
    ap.add_argument("--md", default=None, help="write a RESULTS.md draft here")
    args = ap.parse_args()

    recs, ckpts = [], set()
    for p in args.json_paths:
        d = json.load(open(p))
        if d["config"].get("partial"):
            sys.exit(f"[analyze] {p} is a partial (mid-run) dump — refusing")
        recs.extend(d["records"])
        ckpts.add(d["config"]["ckpt"])
    if len(ckpts) != 1:
        sys.exit(f"[analyze] mixed checkpoints: {ckpts}")
    keys = [r["key"] for r in recs]
    if len(set(keys)) != len(keys):
        sys.exit("[analyze] duplicate sample keys across shards — refusing")
    data = {"config": {"ckpt": ckpts.pop()}}
    pols = [{"key": r["key"], **policies(r)} for r in recs]
    n = len(pols)

    mean = lambda xs: sum(xs) / len(xs)
    dep = mean([p["deployed"] for p in pols])
    ora = mean([p["oracle"] for p in pols])
    gre = mean([p["greedy"] for p in pols])

    gap_od = [p["oracle"] - p["deployed"] for p in pols]
    gap_og = [p["oracle"] - p["greedy"] for p in pols]
    gap_dg = [p["deployed"] - p["greedy"] for p in pols]
    ci_od, ci_og, ci_dg = boot_ci(gap_od), boot_ci(gap_og), boot_ci(gap_dg)

    cov = Counter(str(p["deployed_by"]) for p in pols)
    owin = Counter(str(p["oracle_draw"]) for p in pols)
    n_gain = {t: sum(1 for g in gap_od if g > t) for t in (0.001, 0.01, 0.05, 0.10)}

    lines = []
    w = lines.append
    w(f"n = {n} | ckpt = {data['config']['ckpt']}")
    w(f"deployed (first-exec + repair): mean IoU {dep:.4f}")
    w(f"oracle   (best of 4 draws):     mean IoU {ora:.4f}")
    w(f"greedy   (draw 0, no repair):   mean IoU {gre:.4f}")
    w(f"gap oracle-deployed: {ora-dep:+.4f}  (95% CI [{ci_od[0]:+.4f}, {ci_od[1]:+.4f}])")
    w(f"gap oracle-greedy:   {ora-gre:+.4f}  (95% CI [{ci_og[0]:+.4f}, {ci_og[1]:+.4f}])")
    w(f"gap deployed-greedy: {dep-gre:+.4f}  (95% CI [{ci_dg[0]:+.4f}, {ci_dg[1]:+.4f}])")
    w(f"deployed coverage by draw: {dict(sorted(cov.items()))}")
    w(f"oracle winning draw:       {dict(sorted(owin.items()))}")
    w("samples where oracle beats deployed by > t: "
      + ", ".join(f">{t}: {c}" for t, c in n_gain.items()))
    print("\n".join(lines))

    if not args.md:
        return

    md = []
    m = md.append
    m("## Headline numbers\n")
    m("| Policy | Mean centered IoU |")
    m("|---|---|")
    m(f"| (c) greedy draw 0, no repair | {gre:.4f} |")
    m(f"| (a) deployed: first-executing of 4 + repair | {dep:.4f} |")
    m(f"| (b) oracle: best-IoU of 4 draws | {ora:.4f} |")
    m("")
    m("| Gap (paired, same draws) | Mean | Bootstrap 95% CI |")
    m("|---|---|---|")
    m(f"| oracle − deployed (critic-reranker ceiling) | {ora-dep:+.4f} | [{ci_od[0]:+.4f}, {ci_od[1]:+.4f}] |")
    m(f"| oracle − greedy | {ora-gre:+.4f} | [{ci_og[0]:+.4f}, {ci_og[1]:+.4f}] |")
    m(f"| deployed − greedy | {dep-gre:+.4f} | [{ci_dg[0]:+.4f}, {ci_dg[1]:+.4f}] |")
    m("")
    m("## Which draw wins\n")
    m("| | " + " | ".join(sorted(set(list(cov) + list(owin)))) + " |")
    m("|---|" + "---|" * len(set(list(cov) + list(owin))))
    keys = sorted(set(list(cov) + list(owin)))
    m("| deployed picks | " + " | ".join(str(cov.get(k, 0)) for k in keys) + " |")
    m("| oracle picks | " + " | ".join(str(owin.get(k, 0)) for k in keys) + " |")
    m("")
    m(f"Samples where oracle beats deployed: "
      + ", ".join(f"by >{t}: **{c}**" for t, c in n_gain.items()) + "\n")
    m("## Per-sample table\n")
    m("(draw IoUs; `--` = did not execute; sorted by oracle−deployed gap)\n")
    m("| key | d0 | d1 | d2 | d3 | deployed (by) | oracle (draw) | gap |")
    m("|---|---|---|---|---|---|---|---|")
    fmt = lambda v: "--" if v is None else f"{v:.3f}"
    for p in sorted(pols, key=lambda p: p["deployed"] - p["oracle"]):
        di = p["draw_ious"]
        m(f"| {p['key'][:12]} | {fmt(di.get(0))} | {fmt(di.get(1))} "
          f"| {fmt(di.get(2))} | {fmt(di.get(3))} "
          f"| {p['deployed']:.3f} ({p['deployed_by']}) "
          f"| {p['oracle']:.3f} ({p['oracle_draw']}) "
          f"| {p['oracle']-p['deployed']:+.3f} |")
    with open(args.md, "w") as f:
        f.write("\n".join(md) + "\n")
    print(f"[analyze] wrote {args.md}")


if __name__ == "__main__":
    main()
