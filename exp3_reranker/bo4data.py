"""Exp3 shared data layer: exp1 shard loading + policy evaluation machinery.

A *policy* is a function record -> chosen draw index (int) or None.
- It may only choose among draws with exec_ok=True (enforced here: an illegal
  pick raises). None means "no pick" -> deployed repair fallback (exp1 semantics:
  repair IoU if the repair executed, else 0), identical across policies.
- Evaluation maps the pick to that draw's shard IoU; selection code never sees IoUs.

Paired bootstrap: same 20k-resample scheme as exp1_bestof4_oracle/analyze_bo4.py.
"""
from __future__ import annotations

import glob
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
SHARDS = os.path.join(HERE, "..", "exp1_bestof4_oracle", "artifacts", "shards",
                      "bo4_oracle_w*.json")


def load_records(pattern: str = SHARDS) -> list[dict]:
    recs, ckpts = [], set()
    for p in sorted(glob.glob(pattern)):
        d = json.load(open(p))
        if d["config"].get("partial"):
            raise SystemExit(f"{p} is a partial dump")
        ckpts.add(d["config"]["ckpt"])
        recs.extend(d["records"])
    keys = [r["key"] for r in recs]
    assert len(ckpts) == 1, ckpts
    assert len(keys) == len(set(keys)) == 96, len(keys)
    for r in recs:
        r["draws"].sort(key=lambda d: d["draw"])
        assert [d["draw"] for d in r["draws"]] == [0, 1, 2, 3], r["key"]
    recs.sort(key=lambda r: r["key"])
    return recs


def exec_draws(rec: dict) -> list[dict]:
    return [d for d in rec["draws"] if d["exec_ok"]]


def repair_iou(rec: dict) -> float:
    rep = rec.get("repair")
    return rep["iou_centered"] if rep and rep.get("exec_ok") else 0.0


def first_exec_draw(rec: dict):
    ex = exec_draws(rec)
    return min(ex, key=lambda d: d["draw"])["draw"] if ex else None


def policy_iou(rec: dict, pick) -> float:
    """IoU obtained by choosing draw `pick` (None -> repair fallback)."""
    if pick is None:
        return repair_iou(rec)
    d = rec["draws"][pick]
    assert d["draw"] == pick
    if not d["exec_ok"]:
        raise ValueError(f"{rec['key']}: policy picked non-executing draw {pick}")
    return d["iou_centered"]


# --- baselines ---------------------------------------------------------------

def pick_deployed(rec):
    return first_exec_draw(rec)


def pick_greedy(rec):
    d0 = rec["draws"][0]
    return 0 if d0["exec_ok"] else None


def oracle_iou(rec) -> float:
    ex = exec_draws(rec)
    return max(d["iou_centered"] for d in ex) if ex else repair_iou(rec)


def random_exec_iou(rec) -> float:
    """Analytic expectation of 'uniform random among executing draws'."""
    ex = exec_draws(rec)
    return (sum(d["iou_centered"] for d in ex) / len(ex)) if ex else repair_iou(rec)


# --- evaluation --------------------------------------------------------------

def boot_ci(diffs, iters=20000, seed=0):
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(iters))
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def gross_error_keys(recs, thresh=0.10):
    """Exp1's concentration set: oracle-deployed gap > thresh (18 samples at 0.10)."""
    out = []
    for r in recs:
        dep = policy_iou(r, pick_deployed(r))
        if oracle_iou(r) - dep > thresh:
            out.append(r["key"])
    return set(out)


def evaluate_policy(recs, picks: dict, name="policy", n_model_calls=0, wall_s=0.0):
    """picks: key -> draw index or None. Returns a metrics dict."""
    dep_ious, pol_ious, gaps = {}, {}, {}
    for r in recs:
        k = r["key"]
        dep_ious[k] = policy_iou(r, pick_deployed(r))
        pol_ious[k] = (picks[k] if isinstance(picks[k], float)
                       else policy_iou(r, picks[k]))
        gaps[k] = oracle_iou(r) - dep_ious[k]
    keys = [r["key"] for r in recs]
    n = len(keys)
    diffs = [pol_ious[k] - dep_ious[k] for k in keys]
    mean = lambda xs: sum(xs) / len(xs)
    dep_mean, pol_mean = mean(list(dep_ious.values())), mean(list(pol_ious.values()))
    lo, hi = boot_ci(diffs)
    total_gap = sum(gaps.values())
    gross = {k for k in keys if gaps[k] > 0.10}
    # fixed: on a gross-error sample, policy recovers >=50% of that sample's gap
    fixed = sum(1 for k in gross
                if pol_ious[k] - dep_ious[k] >= 0.5 * gaps[k])
    improved = sum(1 for d in diffs if d > 0.01)
    broken = sum(1 for d in diffs if d < -0.01)
    worst_break = min(diffs)
    return {
        "policy": name, "n": n,
        "mean_iou": round(pol_mean, 4),
        "delta_vs_deployed": round(pol_mean - dep_mean, 4),
        "ci95": [round(lo, 4), round(hi, 4)],
        "significant": bool(lo > 0 or hi < 0),
        "pct_oracle_gap": round(100.0 * (pol_mean - dep_mean) * n / total_gap, 1),
        "gross18_fixed": f"{fixed}/{len(gross)}",
        "n_improved_gt.01": improved, "n_broken_gt.01": broken,
        "worst_single_break": round(worst_break, 4),
        "model_calls": n_model_calls, "wall_s": round(wall_s, 1),
    }


if __name__ == "__main__":
    recs = load_records()
    mean = lambda xs: sum(xs) / len(xs)
    dep = mean([policy_iou(r, pick_deployed(r)) for r in recs])
    ora = mean([oracle_iou(r) for r in recs])
    gre = mean([policy_iou(r, pick_greedy(r)) if pick_greedy(r) is not None else 0.0
                for r in recs])
    # exp1 greedy = draw0 IoU if exec else 0.0 (no repair)
    gre = mean([(r["draws"][0]["iou_centered"] if r["draws"][0]["exec_ok"] else 0.0)
                for r in recs])
    rnd = mean([random_exec_iou(r) for r in recs])
    print(f"deployed {dep:.4f}  oracle {ora:.4f}  greedy {gre:.4f}  random-exec {rnd:.4f}")
    print(f"gross-error(>0.10) samples: {len(gross_error_keys(recs))}")
    print("expect: deployed 0.8756  oracle 0.9222  greedy 0.7871  gross 18")
