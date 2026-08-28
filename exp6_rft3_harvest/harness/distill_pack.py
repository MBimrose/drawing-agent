"""Exp6 stage 6: distill accepted trajectories into rft_v3 seed records and
report harvest economics.

Reads DATA/results_<tag>.jsonl + DATA/trajectories/<tag>/<key>.json and writes

  <exp>/accepted_rft_v3_seed.jsonl   {key, iou, think, code}   (IoU >= 0.8)
  <exp>/nearmiss.jsonl               {key, iou, ss_iou, gen_iou, n_calls,
                                      think, code}             (0.5 <= IoU < 0.8)

Records are exactly the shape vendor pack_rft_shards.py packs (it reads
accepted-*.jsonl with key/iou/think/code and pulls PNGs from tars_v14).

think = the construction plan distilled from the trajectory: the LAST full
plan (>= MIN_FULL chars) among candidate turns up to the accepted (final)
candidate, plus any later shorter plan deltas appended as "Revision:"
paragraphs — so the reading that produced the accepted code is self-contained
even when the final turn's plan only restates a fix. Trajectories keep
everything, so this distillation can be re-run without re-querying the
teacher.

    python3 distill_pack.py [--tag main] [--min-full 600]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
DATA = "/srv/scratch/bimrose2/drawing_agent_exp6"

CODE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(text):
    blocks = CODE_RE.findall(text or "")
    return blocks[-1].strip() + "\n" if blocks else None


def distill_think(record: dict, final_cand: int, min_full: int) -> str:
    cand_turns = [e for e in record["turns"]
                  if e.get("action") == "candidate" and e.get("cand", 0) <= final_cand]
    plans = [(e["cand"], (e.get("plan") or "").strip()) for e in cand_turns]
    plans = [(c, p) for c, p in plans if p]
    if not plans:
        return ""
    full = [(c, p) for c, p in plans if len(p) >= min_full]
    if full:
        base_c, base = full[-1]
    else:
        base_c, base = max(plans, key=lambda t: len(t[1]))
    parts = [base]
    for c, p in plans:
        if c > base_c:
            parts.append("Revision: " + p)
    return "\n\n".join(parts)


def final_code(record: dict, final_cand: int) -> str | None:
    for e in record["turns"]:
        if e.get("action") == "candidate" and e.get("cand") == final_cand:
            return extract_code(e.get("text"))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main")
    ap.add_argument("--min-full", type=int, default=600)
    ap.add_argument("--extra-tags", default=None,
                    help="comma list of additional result tags to merge")
    args = ap.parse_args()

    tags = [args.tag] + ([t for t in args.extra_tags.split(",") if t]
                         if args.extra_tags else [])
    rows, errors = [], 0
    seen = set()
    for tag in tags:
        path = os.path.join(DATA, f"results_{tag}.jsonl")
        with open(path) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if "error" in r:
                    errors += 1
                    continue
                if r["key"] in seen:
                    continue
                seen.add(r["key"])
                r["_tag"] = tag
                rows.append(r)
    print(f"[pack] {len(rows)} scored parts ({errors} errored lines skipped) "
          f"from tags {tags}")

    acc_path = os.path.join(EXP, "accepted_rft_v3_seed.jsonl")
    near_path = os.path.join(EXP, "nearmiss.jsonl")
    acc, near = [], []
    for r in rows:
        iou = r.get("ag_iou", 0.0)
        if iou < 0.5:
            continue
        tpath = os.path.join(DATA, "trajectories", r["_tag"], r["key"] + ".json")
        with open(tpath) as f:
            record = json.load(f)
        fk = r.get("ag_final_cand")
        code = final_code(record, fk) if fk else None
        if code is None:
            print(f"[pack] WARN no final code for {r['key']}")
            continue
        think = distill_think(record, fk, args.min_full)
        rec = {"key": r["key"], "iou": iou, "think": think, "code": code}
        if iou >= 0.8:
            acc.append(rec)
        else:
            near.append({**rec, "ss_iou": r.get("ss_iou"),
                         "gen_iou": r.get("gen_iou"), "n_calls": r.get("n_calls")})

    acc.sort(key=lambda r: r["key"])
    near.sort(key=lambda r: r["key"])
    with open(acc_path, "w") as f:
        for r in acc:
            f.write(json.dumps(r) + "\n")
    with open(near_path, "w") as f:
        for r in near:
            f.write(json.dumps(r) + "\n")

    # ---- economics ----
    n = len(rows)
    ok = [r for r in rows if r.get("ag_iou", 0) >= 0.8]
    calls = sum(r.get("n_calls", 0) for r in rows)
    tin = sum(r.get("tokens", {}).get("in", 0) for r in rows)
    tout = sum(r.get("tokens", {}).get("out", 0) for r in rows)
    wall = sum(r.get("t_total_s", 0) for r in rows)
    print(f"[pack] wrote {acc_path} ({len(acc)} accepted) and "
          f"{near_path} ({len(near)} near-miss)")
    print(f"[stats] acceptance {len(ok)}/{n} = {100*len(ok)/max(n,1):.1f}%  "
          f"near-miss {len(near)}/{n}")
    if ok:
        print(f"[stats] accepted mean IoU {statistics.mean(r['ag_iou'] for r in ok):.3f}")
    if rows:
        print(f"[stats] mean ag IoU (all) "
              f"{statistics.mean(r.get('ag_iou', 0) for r in rows):.3f}  "
              f"ss {statistics.mean(r.get('ss_iou', 0) for r in rows):.3f}")
    print(f"[stats] totals: {calls} calls, {tin/1e6:.2f}M in / {tout/1e6:.2f}M out "
          f"tokens, {wall/3600:.2f} h part-serial wall")
    if ok:
        print(f"[stats] per ACCEPTED trajectory: {calls/len(ok):.1f} calls, "
              f"{tin/1e3/len(ok):.0f}k in / {tout/1e3/len(ok):.0f}k out tokens, "
              f"{wall/60/len(ok):.1f} part-min")


if __name__ == "__main__":
    main()
