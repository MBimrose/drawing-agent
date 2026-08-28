"""Exp6 stage 1-2: compute the eligible reject pool and select the pilot batch.

Pool: rft_v2 seen − accepted (= seen records with iou < 0.8), snapshot under
DATA/rft_v2_snapshot/seen-*.jsonl (133,272 records, 2026-08-28 ~10:50 CDT,
generator e22-combined ckpt-3500, jobs 10182728/9 still running at snapshot).

Filters (data_v14.py semantics, defense-in-depth — rft_generate already skipped
bad/legacy/eval at generation time):
  * exec-bad GT keys        (filters/exec_bad_keys_v14.txt)
  * legacy-renderer keys    (filters/legacy_keys_v14.txt)
  * unplaced-dims keys      (filters/unplaced_keys_v14.txt) — sheet is missing
    required dimensions; unsolvable from the drawing, teacher tokens wasted
  * eval residues: uuid%50==0 (frozen manifest eval) and uuid%50==7 (legacy
    val holdout), uuid = key.rsplit('_v',1)[0], int(uuid[:8],16)

SAMPLING RULE (reproducible + extendable): walk tars_v14 shards in sorted
filename order; within each shard walk member keys in sorted order; keep every
eligible reject; stop after --n keys. Requires the tar files locally (pulled
shard-by-shard until the quota is filled). Extension = same walk, larger --n.

Usage:
  python3 select_batch.py --stats                 # pool numbers only (no tars)
  python3 select_batch.py --n 300                 # select from tars in DATA/tars
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import tarfile

DATA = "/srv/scratch/bimrose2/drawing_agent_exp6"
SNAP = os.path.join(DATA, "rft_v2_snapshot")
FILT = os.path.join(DATA, "filters")
TARS = os.path.join(DATA, "tars")


def uuid_of_key(key: str) -> str:
    return key.rsplit("_v", 1)[0]


def eval_residue(key: str) -> bool:
    try:
        return int(uuid_of_key(key)[:8], 16) % 50 in (0, 7)
    except ValueError:
        return True  # unparseable uuid: exclude


def load_keys(path: str) -> frozenset[str]:
    with open(path) as f:
        return frozenset(ln.strip() for ln in f if ln.strip())


def load_pool() -> tuple[dict[str, float], dict[str, float]]:
    """-> (seen key->iou, eligible-reject key->iou)"""
    seen: dict[str, float] = {}
    for p in sorted(glob.glob(os.path.join(SNAP, "seen-*.jsonl"))):
        with open(p) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    seen[r["key"]] = float(r["iou"])
                except Exception:
                    continue
    bad = load_keys(os.path.join(FILT, "exec_bad_keys_v14.txt"))
    legacy = load_keys(os.path.join(FILT, "legacy_keys_v14.txt"))
    unplaced = load_keys(os.path.join(FILT, "unplaced_keys_v14.txt"))
    rejects = {k: v for k, v in seen.items() if v < 0.8}
    eligible = {k: v for k, v in rejects.items()
                if k not in bad and k not in legacy and k not in unplaced
                and not eval_residue(k)}
    n_res = sum(1 for k in rejects if eval_residue(k))
    print(f"[pool] seen={len(seen)} rejects={len(rejects)} "
          f"({100*len(rejects)/max(len(seen),1):.1f}%)")
    print(f"[pool] reject exclusions: exec-bad={sum(1 for k in rejects if k in bad)} "
          f"legacy={sum(1 for k in rejects if k in legacy)} "
          f"unplaced={sum(1 for k in rejects if k in unplaced)} "
          f"eval-residue={n_res}")
    print(f"[pool] ELIGIBLE rejects={len(eligible)}")
    ious = sorted(eligible.values())
    if ious:
        import statistics
        zero = sum(1 for v in ious if v == 0.0)
        print(f"[pool] eligible iou: mean={statistics.mean(ious):.3f} "
              f"median={ious[len(ious)//2]:.3f} zero={zero} "
              f"({100*zero/len(ious):.0f}%) near-miss 0.5-0.8="
              f"{sum(1 for v in ious if 0.5 <= v < 0.8)}")
    return seen, eligible


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--n", type=int, default=300)
    args = ap.parse_args()

    seen, eligible = load_pool()
    out_pool = os.path.join(DATA, "eligible_rejects.jsonl")
    with open(out_pool, "w") as f:
        for k in sorted(eligible):
            f.write(json.dumps({"key": k, "gen_iou": eligible[k]}) + "\n")
    print(f"[pool] wrote {out_pool}")
    if args.stats:
        return

    picked: list[dict] = []
    shards_used: list[str] = []
    for sp in sorted(glob.glob(os.path.join(TARS, "shard_*.tar"))):
        if len(picked) >= args.n:
            break
        with tarfile.open(sp) as tf:
            names = tf.getnames()
        keys = sorted({n.partition(".")[0] for n in names})
        hits = [k for k in keys if k in eligible]
        # sanity: every member key that passes static filters should be in seen
        # (workers must have finished this shard for the batch to be stable)
        shards_used.append(os.path.basename(sp))
        for k in hits:
            if len(picked) >= args.n:
                break
            picked.append({"key": k, "shard": os.path.basename(sp),
                           "gen_iou": eligible[k]})
        print(f"[select] {os.path.basename(sp)}: {len(hits)} eligible "
              f"(total {len(picked)})")

    out = os.path.join(DATA, "batch_pilot.json")
    with open(out, "w") as f:
        json.dump({"rule": "sorted-shard walk, sorted keys, eligible rejects, "
                           f"first {args.n}",
                   "snapshot": open(os.path.join(SNAP, "SNAPSHOT_TIME.txt")).read().strip(),
                   "generator": "e22-combined/geom_eval/consolidated-checkpoint-3500",
                   "n": len(picked), "shards": shards_used,
                   "parts": picked}, f, indent=1)
    print(f"[select] wrote {out} ({len(picked)} parts from {len(shards_used)} shards)")


if __name__ == "__main__":
    main()
