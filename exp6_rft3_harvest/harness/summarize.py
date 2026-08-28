"""Exp6 analysis tables: harvest yield on the reject pool, by generator-IoU
bucket, plus cost accounting and router-vs-direct smoke comparison.

    python3 summarize.py [--tag main]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st

DATA = "/srv/scratch/bimrose2/drawing_agent_exp6"


def load(tag):
    path = os.path.join(DATA, f"results_{tag}.jsonl")
    rows, errs = [], 0
    if not os.path.exists(path):
        return rows, errs
    seen = set()
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" in r:
                errs += 1
                continue
            if r["key"] in seen:
                continue
            seen.add(r["key"])
            rows.append(r)
    return rows, errs


def mean(xs):
    xs = list(xs)
    return st.mean(xs) if xs else float("nan")


def bucket(r):
    g = r.get("gen_iou") or 0.0
    if g == 0.0:
        return "gen 0.0 (exec/no-code fail)"
    if g < 0.5:
        return "gen (0,0.5)"
    return "gen [0.5,0.8)"


def report(tag):
    rows, errs = load(tag)
    if not rows:
        print(f"== {tag}: no results ==")
        return
    n = len(rows)
    acc = [r for r in rows if r.get("ag_iou", 0) >= 0.8]
    near = [r for r in rows if 0.5 <= r.get("ag_iou", 0) < 0.8]
    print(f"\n== {tag} ==  n={n} (errors pending retry: {errs})")
    print(f"  ss_iou {mean(r['ss_iou'] for r in rows):.3f}   "
          f"ag_iou {mean(r['ag_iou'] for r in rows):.3f}   "
          f"exec {sum(r['ag_exec_ok'] for r in rows)}/{n}")
    print(f"  STaR gate (>=0.8): {len(acc)}/{n} = {100*len(acc)/n:.1f}%   "
          f"near-miss [0.5,0.8): {len(near)}/{n} = {100*len(near)/n:.1f}%")
    if acc:
        print(f"  accepted: mean IoU {mean(r['ag_iou'] for r in acc):.3f}, "
              f"mean calls {mean(r['n_calls'] for r in acc):.1f}")
    print(f"  mean calls {mean(r['n_calls'] for r in rows):.2f}   "
          f"mean t/part {mean(r['t_total_s'] for r in rows):.0f}s   "
          f"tokens/part {mean(r['tokens']['in'] for r in rows)/1e3:.1f}k in / "
          f"{mean(r['tokens']['out'] for r in rows)/1e3:.1f}k out")
    calls = sum(r["n_calls"] for r in rows)
    tin = sum(r["tokens"]["in"] for r in rows)
    tout = sum(r["tokens"]["out"] for r in rows)
    wall = sum(r["t_total_s"] for r in rows)
    if acc:
        print(f"  per ACCEPTED: {calls/len(acc):.1f} calls, "
              f"{tin/1e3/len(acc):.0f}k in / {tout/1e3/len(acc):.0f}k out tok, "
              f"{wall/60/len(acc):.1f} part-min")
    # buckets by generator IoU
    print(f"  {'bucket':<28}{'n':>5}{'ss':>8}{'ag':>8}{'gate':>10}{'near':>8}")
    for b in ("gen 0.0 (exec/no-code fail)", "gen (0,0.5)", "gen [0.5,0.8)"):
        sub = [r for r in rows if bucket(r) == b]
        if not sub:
            continue
        g = sum(1 for r in sub if r["ag_iou"] >= 0.8)
        nm = sum(1 for r in sub if 0.5 <= r["ag_iou"] < 0.8)
        print(f"  {b:<28}{len(sub):>5}{mean(r['ss_iou'] for r in sub):>8.3f}"
              f"{mean(r['ag_iou'] for r in sub):>8.3f}"
              f"{f'{g}/{len(sub)}':>10}{f'{nm}/{len(sub)}':>8}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=None, help="one tag; default: all found")
    args = ap.parse_args()
    if args.tag:
        tags = [args.tag]
    else:
        tags = sorted(fn[len("results_"):-len(".jsonl")]
                      for fn in os.listdir(DATA)
                      if fn.startswith("results_") and fn.endswith(".jsonl"))
    for t in tags:
        report(t)

    # paired smoke comparison if both present
    a, _ = load("smoke_direct")
    b, _ = load("smoke_router")
    common = {r["key"] for r in a} & {r["key"] for r in b}
    if common:
        da = {r["key"]: r for r in a}
        db = {r["key"]: r for r in b}
        print(f"\n== paired smoke: direct vs router (n={len(common)}) ==")
        print(f"  {'key':<14}{'dir ag':>8}{'rtr ag':>8}{'dir t':>8}{'rtr t':>8}"
              f"{'dir out':>9}{'rtr out':>9}")
        for k in sorted(common):
            print(f"  {k[:12]:<14}{da[k]['ag_iou']:>8.3f}{db[k]['ag_iou']:>8.3f}"
                  f"{da[k]['t_total_s']:>8.0f}{db[k]['t_total_s']:>8.0f}"
                  f"{da[k]['tokens']['out']:>9}{db[k]['tokens']['out']:>9}")
        print(f"  mean ag: direct {mean(da[k]['ag_iou'] for k in common):.3f} "
              f"router {mean(db[k]['ag_iou'] for k in common):.3f}; "
              f"mean t: {mean(da[k]['t_total_s'] for k in common):.0f}s vs "
              f"{mean(db[k]['t_total_s'] for k in common):.0f}s")


if __name__ == "__main__":
    main()
