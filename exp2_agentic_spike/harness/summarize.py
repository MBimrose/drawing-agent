"""Aggregate a results.json into the RESULTS.md table + split means.

    python3 harness/summarize.py [results.json]
"""
from __future__ import annotations

import json
import os
import sys

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EXP, "artifacts", "results.json")
    with open(path) as f:
        results = [r for r in json.load(f) if "error" not in r]

    rows = sorted(results, key=lambda r: (r["split"], r["uid"]))
    print("| part | split | single-shot IoU | agentic IoU | delta | best-turn IoU | "
          "model calls | final cand | stop | t_ss (s) | t_agentic (s) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        d = r["ag_iou"] - r["ss_iou"]
        print(f"| {r['uid']} | {r['split']} | {r['ss_iou']:.3f} | {r['ag_iou']:.3f} | "
              f"{d:+.3f} | {r['best_iou']:.3f} | {r['n_calls']} | "
              f"{r['ag_final_cand']} | {r['stop_reason']} | "
              f"{r['t_singleshot_s']:.0f} | {r['t_agentic_s']:.0f} |")

    print()
    for split in ("std", "hard", None):
        sel = [r for r in results if split is None or r["split"] == split]
        name = split or "ALL"
        print(f"**{name}** (n={len(sel)}): single-shot {mean(r['ss_iou'] for r in sel):.3f}"
              f" → agentic {mean(r['ag_iou'] for r in sel):.3f}"
              f" (delta {mean(r['ag_iou'] - r['ss_iou'] for r in sel):+.3f};"
              f" best-turn {mean(r['best_iou'] for r in sel):.3f};"
              f" exec ss {sum(r['ss_exec_ok'] for r in sel)}/{len(sel)},"
              f" ag {sum(r['ag_exec_ok'] for r in sel)}/{len(sel)};"
              f" mean calls {mean(r['n_calls'] for r in sel):.1f};"
              f" mean t_ss {mean(r['t_singleshot_s'] for r in sel):.0f}s,"
              f" t_ag {mean(r['t_agentic_s'] for r in sel):.0f}s)")


if __name__ == "__main__":
    main()
