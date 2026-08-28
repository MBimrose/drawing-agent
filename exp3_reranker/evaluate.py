"""Evaluate all selection policies -> policy_results.json + markdown table.

    /srv/scratch/bimrose2/drawing_agent_exp1/env/bin/python evaluate.py [--vlm vlm_verdicts.json ...]
"""
from __future__ import annotations

import argparse
import json
import math
import os

import bo4data
import policies as P

HERE = os.path.dirname(os.path.abspath(__file__))


def picks_of(pol, recs, ctx):
    return {r["key"]: pol(r, ctx) for r in recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vlm", nargs="*", default=[],
                    help="vlm verdict JSONs (from vlm_critic.py) to evaluate")
    ap.add_argument("--out", default=os.path.join(HERE, "policy_results.json"))
    args = ap.parse_args()

    recs = bo4data.load_records()
    ctx = P.load_ctx()
    rows = []

    def add(name, picks, calls=0, wall=0.0):
        rows.append(bo4data.evaluate_policy(recs, picks, name, calls, wall))

    # --- baselines ---
    add("oracle (ceiling)", {r["key"]: (bo4data.oracle_iou(r) if not bo4data.exec_draws(r)
                                        else max(bo4data.exec_draws(r),
                                                 key=lambda d: d["iou_centered"])["draw"])
                             for r in recs})
    add("deployed (first-exec)", {r["key"]: bo4data.pick_deployed(r) for r in recs})
    add("greedy (draw 0 only)", {r["key"]: (0 if r["draws"][0]["exec_ok"] else None)
                                 for r in recs})
    add("random-exec (expectation)", {r["key"]: bo4data.random_exec_iou(r) for r in recs})

    # --- heuristic singles ---
    add("degenerate-gate only", picks_of(P.pol_degen_only, recs, ctx))
    add("consensus-medoid (always)", picks_of(P.pol_consensus_medoid, recs, ctx))
    add("aspect-best (always)", picks_of(P.pol_aspect_best, recs, ctx))

    # --- gated combinations (ablation) ---
    combos = [
        ("gate: degen", dict(use_degenerate=True, use_consensus=False, use_aspect=False)),
        ("gate: consensus", dict(use_degenerate=False, use_consensus=True, use_aspect=False)),
        ("gate: aspect", dict(use_degenerate=False, use_consensus=False, use_aspect=True)),
        ("gate: degen+consensus", dict(use_degenerate=True, use_consensus=True, use_aspect=False)),
        ("gate: degen+aspect", dict(use_degenerate=True, use_consensus=False, use_aspect=True)),
        ("gate: consensus+aspect", dict(use_degenerate=False, use_consensus=True, use_aspect=True)),
        ("gate: degen+consensus+aspect", dict(use_degenerate=True, use_consensus=True, use_aspect=True)),
    ]
    for name, kw in combos:
        add(name, picks_of(P.make_gated_policy(**kw), recs, ctx))

    # threshold sensitivity for the full gate
    for tau in (0.10, 0.15, 0.20, 0.30):
        for asp in (1.25, 1.35, 1.5):
            pol = P.make_gated_policy(cons_tau=tau, asp_tau=math.log(asp))
            add(f"gate-full tau={tau} asp={asp}", picks_of(pol, recs, ctx))

    # --- combined consensus+aspect score with first-exec margin ---
    for w_cons, w_asp, margin in [(1, 1, 0.05), (1, 1, 0.0), (1, 2, 0.05),
                                  (1, 0, 0.05), (0, 1, 0.05), (1, 1, 0.10)]:
        pol = P.make_combined_policy(w_cons=w_cons, w_asp=w_asp, margin=margin)
        add(f"combined c{w_cons}a{w_asp} m{margin}", picks_of(pol, recs, ctx))

    # --- shape-space consensus (pairwise candidate mesh IoU) ---
    if "pairwise" in ctx:
        for w_shape, w_asp, margin in [(1, 1, 0.05), (1, 1, 0.10), (1, 1, 0.15),
                                       (1, 0, 0.05), (1, 0, 0.10), (1, 1, 0.0),
                                       (1, 2, 0.10), (2, 1, 0.10)]:
            pol = P.make_shape_combined_policy(w_shape, w_asp, margin)
            add(f"shape-comb s{w_shape}a{w_asp} m{margin}", picks_of(pol, recs, ctx))

    # --- VLM verdict files (+ hybrid: heuristic flags, VLM adjudicates) ---
    comb = P.make_combined_policy(w_cons=1, w_asp=1, margin=0.05)
    comb_picks = picks_of(comb, recs, ctx)
    dep_picks = {r["key"]: bo4data.pick_deployed(r) for r in recs}
    for vf in args.vlm:
        d = json.load(open(vf))
        base = os.path.basename(vf).replace(".json", "").replace("vlm_", "vlm:")
        for pol_name, picks in d["policies"].items():
            add(f"{base}:{pol_name}", {k: picks[k] for k in picks},
                calls=d.get("n_calls", 0), wall=d.get("wall_s", 0.0))
        # hybrid: only samples where the heuristic switches go to the VLM
        vlm_pick = d["policies"]["vlm-pick"]
        hybrid, n_h = {}, 0
        for r in recs:
            k = r["key"]
            if comb_picks[k] != dep_picks[k]:
                n_h += 1
                hybrid[k] = vlm_pick.get(k, comb_picks[k])
            else:
                hybrid[k] = dep_picks[k]
        add(f"{base}:hybrid(heur-flag->vlm)", hybrid, calls=n_h)
        # hybrid2: heuristic switches, but VLM must agree it's not the first pick
        hybrid2 = {}
        for r in recs:
            k = r["key"]
            if comb_picks[k] != dep_picks[k] and vlm_pick.get(k) != dep_picks[k]:
                hybrid2[k] = comb_picks[k]
            else:
                hybrid2[k] = dep_picks[k]
        add(f"{base}:hybrid2(heur&vlm-agree)", hybrid2, calls=n_h)

    rows.sort(key=lambda r: -r["mean_iou"])
    with open(args.out, "w") as f:
        json.dump(rows, f, indent=1)

    hdr = ["policy", "mean_iou", "delta_vs_deployed", "ci95", "significant",
           "pct_oracle_gap", "gross18_fixed", "n_improved_gt.01", "n_broken_gt.01",
           "worst_single_break", "model_calls"]
    print(" | ".join(hdr))
    for r in rows:
        print(" | ".join(str(r[h]) for h in hdr))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
