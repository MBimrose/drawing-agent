"""Exp 5 analysis: champion-loop vs greedy / deployed best-of-4 / oracle (CPU, stdlib).

    python3 analyze_loop.py out_loop/loop_w*.json \
        --bo4 ../exp1_bestof4_oracle/bo4_oracle_summary.json \
        [--md table.md] [--summary loop_summary.json]

Merges per-worker loop JSONs, pairs per-sample with exp1's three policies,
and reports: parity of turn-1 vs exp1 greedy d0, paired deltas with bootstrap
95% CIs, rescues/refinements/regressions, final-vs-best (keep-best policy),
rounds/stop-reason histograms, STaR gate yield, and cost.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter

EPS = 1e-4


def boot_ci(diffs, iters=20000, seed=0):
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(iters))
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_paths", nargs="+")
    ap.add_argument("--bo4", required=True,
                    help="exp1 bo4_oracle_summary.json (paired per-sample)")
    ap.add_argument("--md", default=None)
    ap.add_argument("--summary", default=None,
                    help="write merged per-sample summary JSON here")
    args = ap.parse_args()

    recs, cfgs, wall = [], [], []
    for p in args.json_paths:
        d = json.load(open(p))
        if d["config"].get("partial"):
            sys.exit(f"[analyze] {p} is a partial dump — refusing")
        recs.extend(d["records"])
        cfgs.append(d["config"])
        wall.append(d["config"].get("wall_s", 0.0))
    keys = [r["key"] for r in recs]
    if len(set(keys)) != len(keys):
        sys.exit("[analyze] duplicate keys across shards")

    bo4 = {r["key"]: r for r in json.load(open(args.bo4))["records"]}
    missing = [k for k in keys if k not in bo4]
    if missing:
        sys.exit(f"[analyze] {len(missing)} keys not in bo4 summary")

    rows = []
    for r in sorted(recs, key=lambda r: r["key"]):
        s = r["summary"]
        b = bo4[r["key"]]
        cands = [e for e in r["rounds"] if e.get("action") == "candidate"]
        rows.append({
            "key": r["key"],
            "greedy": s["greedy_iou"], "greedy_exec": s["greedy_exec_ok"],
            "final": s["final_iou"], "final_round": s["final_round"],
            "best": s["best_iou"], "best_round": s["best_round"],
            "n_calls": r["n_model_calls"], "n_cands": len(cands),
            "stop": r["stop_reason"],
            "exp1_greedy": b["greedy_iou"], "exp1_deployed": b["deployed_iou"],
            "exp1_oracle": b["oracle_iou"],
        })
    n = len(rows)
    mean = lambda xs: sum(xs) / len(xs)

    # parity: our turn-1 vs exp1 rerun draw 0
    par = [abs(r["greedy"] - r["exp1_greedy"]) for r in rows]
    n_exact = sum(1 for d in par if d < 1e-9)

    g = mean([r["greedy"] for r in rows])
    f = mean([r["final"] for r in rows])
    bst = mean([r["best"] for r in rows])
    dep = mean([r["exp1_deployed"] for r in rows])
    ora = mean([r["exp1_oracle"] for r in rows])

    d_fg = [r["final"] - r["greedy"] for r in rows]
    d_fd = [r["final"] - r["exp1_deployed"] for r in rows]
    d_fo = [r["final"] - r["exp1_oracle"] for r in rows]
    d_bg = [r["best"] - r["greedy"] for r in rows]
    d_bd = [r["best"] - r["exp1_deployed"] for r in rows]
    ci_fg, ci_fd, ci_fo = boot_ci(d_fg), boot_ci(d_fd), boot_ci(d_fo)
    ci_bg, ci_bd = boot_ci(d_bg), boot_ci(d_bd)

    rescues = [r for r in rows if not r["greedy_exec"] and r["final_round"] is not None]
    refined = [r for r in rows if r["greedy_exec"] and r["final"] > r["greedy"] + EPS]
    regress = [r for r in rows if r["final"] < r["greedy"] - EPS]
    worse_than_best = [r for r in rows if r["final"] < r["best"] - EPS]
    stops = Counter(r["stop"] for r in rows)
    calls = Counter(r["n_calls"] for r in rows)
    gate_g = sum(1 for r in rows if r["greedy"] >= 0.8)
    gate_f = sum(1 for r in rows if r["final"] >= 0.8)
    gate_b = sum(1 for r in rows if r["best"] >= 0.8)
    total_calls = sum(r["n_calls"] for r in rows)
    gpu_h = sum(wall) / 3600.0

    out = []
    w = out.append
    w(f"n = {n} | shards = {len(cfgs)} | render = "
      f"{Counter(c.get('render') for c in cfgs)}")
    w(f"turn-1 parity vs exp1 d0: median|diff| = {sorted(par)[n // 2]:.6f}, "
      f"max = {max(par):.6f}, exact = {n_exact}/{n}")
    w("")
    w(f"greedy turn-1        : {g:.4f}   (exp1 greedy {mean([r['exp1_greedy'] for r in rows]):.4f})")
    w(f"loop final           : {f:.4f}")
    w(f"loop best-seen       : {bst:.4f}   (keep-best policy)")
    w(f"exp1 deployed bo4+rep: {dep:.4f}")
    w(f"exp1 oracle-of-4     : {ora:.4f}")
    w("")
    w(f"final - greedy   : {f - g:+.4f}  CI [{ci_fg[0]:+.4f}, {ci_fg[1]:+.4f}]")
    w(f"final - deployed : {f - dep:+.4f}  CI [{ci_fd[0]:+.4f}, {ci_fd[1]:+.4f}]")
    w(f"final - oracle   : {f - ora:+.4f}  CI [{ci_fo[0]:+.4f}, {ci_fo[1]:+.4f}]")
    w(f"best  - greedy   : {bst - g:+.4f}  CI [{ci_bg[0]:+.4f}, {ci_bg[1]:+.4f}]")
    w(f"best  - deployed : {bst - dep:+.4f}  CI [{ci_bd[0]:+.4f}, {ci_bd[1]:+.4f}]")
    w("")
    def moves(rs):
        return ", ".join("{}:{:.3f}->{:.3f}".format(r["key"][:8], r["greedy"],
                                                    r["final"]) for r in rs)

    w(f"rescues (turn-1 exec fail -> working final): {len(rescues)} "
      f"({', '.join(r['key'][:8] for r in rescues)})")
    w(f"refinements (working turn-1 improved): {len(refined)} ({moves(refined)})")
    w(f"regressions (final < turn-1): {len(regress)} ({moves(regress)})")
    w(f"final < best-seen: {len(worse_than_best)} (mean gap over those: "
      f"{mean([r['best'] - r['final'] for r in worse_than_best]) if worse_than_best else 0:.4f})")
    w(f"stop reasons: {dict(stops)}")
    w(f"model calls histogram: {dict(sorted(calls.items()))} "
      f"(mean {total_calls / n:.2f}, total {total_calls})")
    w(f"STaR gate (IoU>=0.8): greedy {gate_g}/{n} -> final {gate_f}/{n} "
      f"(best {gate_b}/{n})")
    w(f"cost: max worker wall {max(wall) / 60:.1f} min, {gpu_h:.2f} GPU-hours "
      f"(exp1 best-of-4: ~19 min x 16 = ~5.1 GPU-h)")
    print("\n".join(out))

    if args.summary:
        with open(args.summary, "w") as fh:
            json.dump({"config": {"ckpt": cfgs[0]["ckpt"],
                                  "max_rounds": cfgs[0]["max_rounds"],
                                  "render": [c.get("render") for c in cfgs],
                                  "wall_s_per_worker": wall},
                       "records": rows}, fh, indent=1)
        print(f"[analyze] wrote {args.summary}")

    if args.md:
        md = ["| key | turn-1 | loop final (rd) | best (rd) | Δloop | deployed | oracle | stop |",
              "|---|---|---|---|---|---|---|---|"]
        for r in sorted(rows, key=lambda r: r["final"] - r["greedy"],
                        reverse=True):
            md.append(
                f"| {r['key'][:12]} | {r['greedy']:.3f} | "
                f"{r['final']:.3f} ({r['final_round']}) | "
                f"{r['best']:.3f} ({r['best_round']}) | "
                f"{r['final'] - r['greedy']:+.3f} | {r['exp1_deployed']:.3f} | "
                f"{r['exp1_oracle']:.3f} | {r['stop']} |")
        with open(args.md, "w") as fh:
            fh.write("\n".join(md) + "\n")
        print(f"[analyze] wrote {args.md}")


if __name__ == "__main__":
    main()
