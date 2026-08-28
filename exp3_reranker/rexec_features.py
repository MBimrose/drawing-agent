"""Re-execute all 384 exp1 candidates CPU-parallel; extract geometry features.

    /srv/scratch/bimrose2/drawing_agent_exp1/env/bin/python rexec_features.py [--workers 48]

Writes code/STL/STEP to /srv/scratch/bimrose2/drawing_agent_exp3/candidates/ (outside
repo) and a compact features.json here (committed). Cross-checks re-exec exec_ok vs the
shards' exec_ok and (where available) volume vs exp1's persisted STLs.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import bo4data

HERE = os.path.dirname(os.path.abspath(__file__))
PY = "/srv/scratch/bimrose2/drawing_agent_exp1/env/bin/python"
WORKER = os.path.join(HERE, "_exec_measure_one.py")
WORK = "/srv/scratch/bimrose2/drawing_agent_exp3/candidates"
EXP1_CANDS = "/srv/scratch/bimrose2/drawing_agent_exp1/out_bo4_oracle/candidates"


def run_one(tag: str, code: str):
    os.makedirs(WORK, exist_ok=True)
    py = os.path.join(WORK, f"{tag}.py")
    stl = os.path.join(WORK, f"{tag}.stl")
    step = os.path.join(WORK, f"{tag}.step")
    with open(py, "w") as f:
        f.write(code)
    t0 = time.time()
    try:
        r = subprocess.run([PY, WORKER, py, stl, step],
                           capture_output=True, text=True, timeout=300)
        out = r.stdout.strip().splitlines()
        rec = json.loads(out[-1]) if out else {"exec_ok": False, "error": "no output"}
    except subprocess.TimeoutExpired:
        rec = {"exec_ok": False, "error": "timeout 300s"}
    except Exception as e:  # noqa: BLE001
        rec = {"exec_ok": False, "error": repr(e)[:300]}
    rec["t_s"] = round(time.time() - t0, 1)
    return tag, rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=48)
    args = ap.parse_args()

    recs = bo4data.load_records()
    jobs = []
    shard_exec = {}
    for r in recs:
        for d in r["draws"]:
            tag = d["tag"]
            jobs.append((tag, d["code"]))
            shard_exec[tag] = d["exec_ok"]

    t0 = time.time()
    feats = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_one, t, c): t for t, c in jobs}
        done = 0
        for fut in as_completed(futs):
            tag, rec = fut.result()
            feats[tag] = rec
            done += 1
            if done % 50 == 0:
                print(f"[{done}/{len(jobs)}] {time.time()-t0:.0f}s", flush=True)

    wall = time.time() - t0
    agree = sum(1 for t in shard_exec if feats[t]["exec_ok"] == shard_exec[t])
    mismatch = [t for t in shard_exec if feats[t]["exec_ok"] != shard_exec[t]]
    print(f"re-exec done in {wall:.0f}s: exec_ok agreement {agree}/{len(shard_exec)}")
    for t in mismatch:
        print(f"  MISMATCH {t}: shard={shard_exec[t]} rexec={feats[t]['exec_ok']} "
              f"err={feats[t].get('error','')[:120]}")

    # volume cross-check vs exp1's persisted STLs (workers 0-7 on this box)
    try:
        import trimesh
        diffs, n_cmp = [], 0
        for t, rec in feats.items():
            p = os.path.join(EXP1_CANDS, f"{t}.stl")
            if rec.get("exec_ok") and os.path.exists(p):
                v0 = abs(trimesh.load(p, force="mesh").volume)
                v1 = rec["volume_mm3"]
                if v0 > 0:
                    diffs.append(abs(v1 - v0) / v0)
                n_cmp += 1
        if diffs:
            diffs.sort()
            print(f"volume vs exp1 STLs: n={n_cmp} median relΔ={diffs[len(diffs)//2]:.2e} "
                  f"max relΔ={diffs[-1]:.2e}")
    except Exception as e:  # noqa: BLE001
        print("volume cross-check skipped:", repr(e)[:200])

    out = os.path.join(HERE, "features.json")
    with open(out, "w") as f:
        json.dump({"wall_s": round(wall, 1), "workers": args.workers,
                   "features": feats}, f, indent=0, sort_keys=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
