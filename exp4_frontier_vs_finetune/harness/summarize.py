"""Exp4 analysis: Kimi arms vs the e24-rft champion, paired per sample.

    python3 harness/summarize.py [results.json] [--md]

Merges results.json with exp1's bo4_oracle_summary.json (same 96 samples) and
prints: means, exec rates, STaR-gate yield, paired deltas with bootstrap CIs,
champion-difficulty buckets, cost table, and the per-sample markdown table.
"""
from __future__ import annotations

import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
REPO = os.path.dirname(EXP)
EXP1_SUMMARY = os.path.join(REPO, "exp1_bestof4_oracle", "bo4_oracle_summary.json")


def boot_ci(deltas, n=20000, seed=0):
    rng = random.Random(seed)
    m = len(deltas)
    means = sorted(sum(rng.choices(deltas, k=m)) / m for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="?", default=os.path.join(EXP, "results.json"))
    args = ap.parse_args()

    with open(args.results) as f:
        res = {r["uid"]: r for r in json.load(f) if "error" not in r}
    errs = []
    with open(args.results) as f:
        errs = [r["uid"] for r in json.load(f) if "error" in r]
    with open(EXP1_SUMMARY) as f:
        champ = {r["key"]: r for r in json.load(f)["records"]}

    keys = sorted(set(res) & set(champ))
    print(f"n = {len(keys)} (errors: {len(errs)})")
    if errs:
        print("ERRORED:", errs)

    ss = [res[k]["ss_iou"] for k in keys]
    ag = [res[k]["ag_iou"] for k in keys]
    best = [res[k]["best_iou"] for k in keys]
    greedy = [champ[k]["greedy_iou"] for k in keys]
    dep = [champ[k]["deployed_iou"] for k in keys]
    ora = [champ[k]["oracle_iou"] for k in keys]

    print("\n== Means (centered IoU) ==")
    rows = [("kimi single-shot", ss), ("kimi agentic", ag),
            ("kimi agentic best-cand (oracle-ish)", best),
            ("champ greedy", greedy), ("champ deployed bo4+repair", dep),
            ("champ oracle-of-4", ora)]
    for name, xs in rows:
        ge8 = sum(1 for x in xs if x >= 0.8)
        print(f"  {name:38s} {mean(xs):.4f}   IoU>=0.8: {ge8}/{len(xs)}")

    print("\n== Exec success ==")
    print(f"  kimi ss exec: {sum(res[k]['ss_exec_ok'] for k in keys)}/{len(keys)}")
    print(f"  kimi ag exec: {sum(res[k]['ag_exec_ok'] for k in keys)}/{len(keys)}")

    print("\n== Paired deltas (bootstrap 95% CI) ==")
    for name, a, b in [("kimi_ag - kimi_ss", ag, ss),
                       ("kimi_ag - champ_greedy", ag, greedy),
                       ("kimi_ag - champ_deployed", ag, dep),
                       ("kimi_ag - champ_oracle", ag, ora),
                       ("kimi_ss - champ_greedy", ss, greedy),
                       ("kimi_best - champ_oracle", best, ora)]:
        d = [x - y for x, y in zip(a, b)]
        lo, hi = boot_ci(d)
        wins = sum(1 for x in d if x > 0.001)
        losses = sum(1 for x in d if x < -0.001)
        print(f"  {name:26s} {mean(d):+.4f}  CI [{lo:+.4f}, {hi:+.4f}]  "
              f"win/tie/loss {wins}/{len(d)-wins-losses}/{losses}")

    print("\n== Champion-difficulty buckets (by champ deployed IoU) ==")
    buckets = [("champ-solved  (dep>=0.95)", lambda v: v >= 0.95),
               ("champ-partial (0.8<=dep<0.95)", lambda v: 0.8 <= v < 0.95),
               ("champ-hard    (dep<0.8)", lambda v: v < 0.8)]
    print(f"  {'bucket':32s} {'n':>3s} {'kimi_ss':>8s} {'kimi_ag':>8s} "
          f"{'champ_dep':>9s} {'champ_ora':>9s}")
    for name, pred in buckets:
        sel = [k for k in keys if pred(champ[k]["deployed_iou"])]
        if not sel:
            continue
        print(f"  {name:32s} {len(sel):3d} "
              f"{mean([res[k]['ss_iou'] for k in sel]):8.3f} "
              f"{mean([res[k]['ag_iou'] for k in sel]):8.3f} "
              f"{mean([champ[k]['deployed_iou'] for k in sel]):9.3f} "
              f"{mean([champ[k]['oracle_iou'] for k in sel]):9.3f}")

    print("\n== Cost per part (kimi) ==")
    calls = [res[k]["n_calls"] for k in keys]
    t_ss = [res[k]["t_singleshot_s"] for k in keys]
    t_ag = [res[k]["t_agentic_s"] for k in keys]
    ti = [res[k]["total_tokens"]["in"] for k in keys]
    to = [res[k]["total_tokens"]["out"] for k in keys]
    si = [res[k]["ss_tokens"]["in"] for k in keys]
    so = [res[k]["ss_tokens"]["out"] for k in keys]
    print(f"  calls: mean {mean(calls):.2f}  max {max(calls)}")
    print(f"  wall-clock: ss mean {mean(t_ss):.0f}s, agentic mean {mean(t_ag):.0f}s")
    print(f"  tokens ss: in {mean(si):.0f} out {mean(so):.0f}; "
          f"agentic total: in {mean(ti):.0f} out {mean(to):.0f}")
    stops = {}
    for k in keys:
        stops[res[k]["stop_reason"]] = stops.get(res[k]["stop_reason"], 0) + 1
    print(f"  stop reasons: {stops}")
    gap = [res[k]["best_iou"] - res[k]["ag_iou"] for k in keys]
    print(f"  best-cand minus FINAL: mean {mean(gap):+.4f}  max {max(gap):+.4f}")

    print("\n== Per-sample table (markdown) ==")
    print("| key | kimi ss | kimi ag | calls | champ greedy | champ dep | champ ora |"
          " ag−dep |")
    print("|---|---|---|---|---|---|---|---|")
    for k in sorted(keys, key=lambda k: res[k]["ag_iou"] - champ[k]["deployed_iou"]):
        r, c = res[k], champ[k]
        print(f"| {k[:12]} | {r['ss_iou']:.3f} | {r['ag_iou']:.3f} | {r['n_calls']} "
              f"| {c['greedy_iou']:.3f} | {c['deployed_iou']:.3f} "
              f"| {c['oracle_iou']:.3f} | {r['ag_iou']-c['deployed_iou']:+.3f} |")


if __name__ == "__main__":
    main()
