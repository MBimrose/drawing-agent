"""Render 3-view PNGs for every executing candidate (CPU-parallel).

    python3 render_candidates.py [--workers 48]

Reads STEPs from /srv/scratch/bimrose2/drawing_agent_exp3/candidates/,
writes PNGs to /srv/scratch/bimrose2/drawing_agent_exp3/renders/<tag>.png.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bo4data  # noqa: E402

PY = "/software/python-3.11.1/bin/python3.11"
RENDER = os.path.join(HERE, "_render_one.py")
CANDS = "/srv/scratch/bimrose2/drawing_agent_exp3/candidates"
OUT = "/srv/scratch/bimrose2/drawing_agent_exp3/renders"


def run_one(tag):
    step = os.path.join(CANDS, f"{tag}.step")
    png = os.path.join(OUT, f"{tag}.png")
    if os.path.exists(png) and os.path.getsize(png) > 0:
        return tag, True, "cached"
    if not os.path.exists(step):
        return tag, False, "no step"
    try:
        r = subprocess.run([PY, RENDER, step, png], capture_output=True,
                           text=True, timeout=300)
        ok = r.returncode == 0 and os.path.exists(png) and os.path.getsize(png) > 0
        return tag, ok, (r.stderr or "")[-200:] if not ok else ""
    except subprocess.TimeoutExpired:
        return tag, False, "timeout"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=48)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    recs = bo4data.load_records()
    tags = [d["tag"] for r in recs for d in bo4data.exec_draws(r)]
    t0 = time.time()
    status = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(run_one, t) for t in tags]
        for i, fut in enumerate(as_completed(futs)):
            tag, ok, msg = fut.result()
            status[tag] = ok
            if not ok:
                print(f"FAIL {tag}: {msg}", flush=True)
            if (i + 1) % 50 == 0:
                print(f"[{i+1}/{len(tags)}] {time.time()-t0:.0f}s", flush=True)
    n_ok = sum(status.values())
    print(f"rendered {n_ok}/{len(tags)} in {time.time()-t0:.0f}s")
    with open(os.path.join(HERE, "artifacts", "render_status.json"), "w") as f:
        json.dump(status, f, indent=0, sort_keys=True)


if __name__ == "__main__":
    main()
