"""Diagnostics for a VLM verdict file: agreement with oracle, score-vs-IoU signal.

    /srv/scratch/bimrose2/drawing_agent_exp1/env/bin/python vlm_diag.py artifacts/vlm_kimi.json
"""
from __future__ import annotations

import json
import sys

import bo4data


def main(path):
    d = json.load(open(path))
    recs = {r["key"]: r for r in bo4data.load_records()}
    n = agree_oracle = agree_dep = parse_fail = 0
    gross_flags_right = gross_flags_wrong = 0
    pairs = []          # (score, iou) per candidate
    for key, res in d["results"].items():
        r = recs[key]
        v = res.get("verdict")
        if not v:
            parse_fail += "skipped" not in res
            continue
        n += 1
        letter_of = {int(k): l for k, l in res["letter_of"].items()}
        of_letter = {l: k for k, l in letter_of.items()}
        ex = {dd["draw"]: dd["iou_centered"] for dd in bo4data.exec_draws(r)}
        oracle_draw = max(ex, key=ex.get)
        first = bo4data.first_exec_draw(r)
        pick = of_letter.get(v["best"])
        if pick is not None:
            agree_oracle += abs(ex[pick] - ex[oracle_draw]) < 1e-9
            agree_dep += pick == first
        for l, s in v["scores"].items():
            if l in of_letter:
                pairs.append((s, ex[of_letter[l]]))
        for l in v["gross"]:
            if l in of_letter:
                # a "gross" flag is right if that candidate is >=0.10 below the best
                if ex[of_letter[l]] <= ex[oracle_draw] - 0.10:
                    gross_flags_right += 1
                else:
                    gross_flags_wrong += 1
    print(f"verdicts {n}; parse failures {parse_fail}")
    print(f"picked-an-oracle-best draw: {agree_oracle}/{n}; picked first-exec: {agree_dep}/{n}")
    print(f"gross flags: {gross_flags_right} right / {gross_flags_wrong} wrong "
          f"(right = flagged draw >=0.10 below sibling best)")
    # score-vs-IoU: mean IoU by score bucket
    from collections import defaultdict
    b = defaultdict(list)
    for s, iou in pairs:
        b[int(s)].append(iou)
    print("score bucket -> n, mean IoU:")
    for s in sorted(b):
        print(f"  {s:2d}: n={len(b[s]):3d} mean={sum(b[s])/len(b[s]):.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
