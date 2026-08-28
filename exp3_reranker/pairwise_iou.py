"""Pairwise candidate-vs-candidate centered volumetric IoU (NO GT involved).

Shape-space consensus: bbox/volume consensus is blind to internal features (holes,
pockets, ribs) — most unfixed gross-error samples have identical bboxes across draws.
Candidate-pair mesh IoU sees those differences.

    /srv/scratch/bimrose2/drawing_agent_exp1/env/bin/python pairwise_iou.py [--workers 48]

Writes pairwise_iou.json here (committed): key -> {"i-j": iou_centered}.
Uses the vendor metric implementation via exp2_agentic_spike/harness/iou.py.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bo4data  # noqa: E402

PY = "/srv/scratch/bimrose2/drawing_agent_exp1/env/bin/python"
IOU = os.path.join(HERE, "..", "exp2_agentic_spike", "harness", "iou.py")
CANDS = "/srv/scratch/bimrose2/drawing_agent_exp3/candidates"


def one_pair(key, i, j, stl_i, stl_j):
    try:
        r = subprocess.run([PY, IOU, stl_i, stl_j], capture_output=True,
                           text=True, timeout=300)
        rec = json.loads(r.stdout.strip().splitlines()[-1])
        return key, i, j, rec["iou_centered"]
    except Exception:  # noqa: BLE001
        return key, i, j, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=48)
    args = ap.parse_args()
    recs = bo4data.load_records()
    jobs = []
    for r in recs:
        ex = bo4data.exec_draws(r)
        for a, b in itertools.combinations(ex, 2):
            sa = os.path.join(CANDS, a["tag"] + ".stl")
            sb = os.path.join(CANDS, b["tag"] + ".stl")
            if os.path.exists(sa) and os.path.exists(sb):
                jobs.append((r["key"], a["draw"], b["draw"], sa, sb))
    print(f"{len(jobs)} pairs")
    t0 = time.time()
    out = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(one_pair, *j) for j in jobs]
        for n, fut in enumerate(as_completed(futs)):
            key, i, j, iou = fut.result()
            out.setdefault(key, {})[f"{i}-{j}"] = iou
            if (n + 1) % 100 == 0:
                print(f"[{n+1}/{len(jobs)}] {time.time()-t0:.0f}s", flush=True)
    with open(os.path.join(HERE, "pairwise_iou.json"), "w") as f:
        json.dump(out, f, indent=0, sort_keys=True)
    print(f"done in {time.time()-t0:.0f}s; wrote pairwise_iou.json")


if __name__ == "__main__":
    main()
