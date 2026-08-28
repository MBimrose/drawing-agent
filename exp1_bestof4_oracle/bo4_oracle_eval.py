"""Exp 1 — all-draws best-of-4 eval with per-draw scoring (oracle-gap study).

Differences from vendor bestofn_eval.py (drawing-vlm train_v14/geom):
  * NO early stop: every sample gets all k draws generated, executed and
    IoU-scored independently (bestofn_eval skips solved samples, keeps only
    the first executing draw's STL in a TemporaryDirectory, and discards the
    candidate code — so the oracle is NOT computable from its output).
  * Persists per-draw candidate code (inline in the output JSON and as .py
    files), exec outcome and centered/raw IoU.
  * Computes three policies from the SAME draws (paired comparison):
      deployed  first draw that executes, one greedy repair round if none
                (mirrors the deployed best-of-4 policy)
      oracle    highest-IoU executing draw (repair fallback if none execute)
      greedy    draw 0 only, no repair
  * Read-only against the drawing-vlm repo and runs/: refuses to trigger a
    DCP consolidation (requires a pre-existing consolidated dir), writes
    only under --out.

Run on the campus cluster (see exp1_bo4_oracle.sbatch):

    python bo4_oracle_eval.py --run e24-rft \
        --ckpt .../runs/e24-rft/checkpoint-3250 --out <fresh_out_dir>
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

TRAIN = os.environ.get(
    "DRAWING_VLM_TRAIN",
    "/projects/illinois/eng/ece/wpk/bimrose2/drawing_vlm/train_v14")
sys.path.insert(0, TRAIN)
sys.path.insert(0, os.path.join(TRAIN, "geom"))

from data_v14 import EVAL_CACHE, EVAL_CACHE_V15, _decode_png  # noqa: E402
from geom_eval_worker import (  # noqa: E402
    build_gen_messages, build_repair_messages, classify_ckpt, exec_code,
    extract_code, feedback_text, load_model, run_config,
)
from iou import iou_pair  # noqa: E402


def resolve_ckpt(path: str) -> tuple[str, str]:
    """(usable_path, kind) — never writes into the run dir."""
    kind = classify_ckpt(path)
    if kind == "dcp":
        cons = os.path.join(os.path.dirname(path), "geom_eval",
                            f"consolidated-{os.path.basename(path)}")
        if os.path.exists(os.path.join(cons, "model.safetensors.index.json")):
            return cons, "hf"
        sys.exit(f"[exp1] {path} is DCP with no existing consolidated dir "
                 f"({cons}); refusing to consolidate (read-only policy). "
                 f"Run their geom eval once, or consolidate into a scratch "
                 f"dir manually.")
    if kind == "unknown":
        sys.exit(f"[exp1] cannot classify checkpoint format at {path}")
    return path, kind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--n", type=int, default=96)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=2400)
    ap.add_argument("--out", required=True, help="fresh output dir")
    ap.add_argument("--worker", type=int, default=0,
                    help="shard id: takes keys[worker::stride] of the pool")
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--model-base", default=None,
                    help="override cfg model_id (processor source) with a "
                         "local copy of the base model dir")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cand_dir = os.path.join(args.out, "candidates")
    os.makedirs(cand_dir, exist_ok=True)

    cfg = run_config(args.run)
    if cfg is None:
        sys.exit(f"[exp1] no config for run {args.run}")
    # Same pool selection as bestofn_eval.py.
    if int(cfg.get("data_version", 1)) == 2:
        cache_path, pool = EVAL_CACHE_V15, "certified"
        gt_dir = os.path.join(os.path.dirname(EVAL_CACHE), "gt_meshes_v15")
    else:
        cache_path, pool = EVAL_CACHE, "all"
        gt_dir = os.path.join(os.path.dirname(EVAL_CACHE), "gt_meshes_v14")

    with open(cache_path, "rb") as f:
        cache = pickle.load(f)
    keys = [k for k in cache["pools"][pool]
            if os.path.exists(os.path.join(gt_dir, f"{k}.stl"))][: args.n]
    keys = keys[args.worker::args.stride]     # this worker's shard
    samples = [{"uuid": k, "image": _decode_png(cache["samples"][k]["png"])}
               for k in keys]
    print(f"[exp1] w{args.worker}/{args.stride}: {len(samples)} samples, "
          f"pool={pool}, T={args.temperature}, k={args.k}", flush=True)

    if args.model_base:
        cfg["model_id"] = args.model_base
    ckpt_path, kind = resolve_ckpt(args.ckpt)
    print(f"[exp1] loading {ckpt_path} ({kind})", flush=True)
    model, processor = load_model(ckpt_path, kind, cfg)

    import torch
    from qwen_vl_utils import process_vision_info

    def gen_batch(msgs_list, sample_mode):
        tmpl = dict(enable_thinking=True,
                    reasoning_effort=cfg.get("reasoning_effort", "medium")) \
            if cfg.get("trace_style", "think") == "think" else {}
        texts = [processor.apply_chat_template(
            m, add_generation_prompt=True, tokenize=False, **tmpl)
            for m in msgs_list]
        images, videos = process_vision_info(msgs_list)
        enc = processor(text=texts, images=images, videos=videos,
                        return_tensors="pt", padding=True)
        enc = {k2: (v.to(model.device) if hasattr(v, "to") else v)
               for k2, v in enc.items()}
        kw = dict(max_new_tokens=args.max_new_tokens,
                  pad_token_id=processor.tokenizer.pad_token_id
                  or processor.tokenizer.eos_token_id)
        if sample_mode:
            kw.update(do_sample=True, temperature=args.temperature, top_p=0.95)
        else:
            kw["do_sample"] = False
        with torch.no_grad():
            out = model.generate(**enc, **kw)
        gen = out[:, enc["input_ids"].shape[1]:]
        return processor.tokenizer.batch_decode(gen, skip_special_tokens=True)

    recs = [{"key": s["uuid"], "draws": [], "repair": None} for s in samples]
    pool_ex = ThreadPoolExecutor(max_workers=8)

    def exec_and_score(key: str, tag: str, code: str | None,
                       reply_tail: str) -> dict:
        """One candidate: write code, execute via harness, IoU vs GT."""
        d: dict = {"tag": tag, "code": code, "exec_ok": False,
                   "exec_rc": None, "stderr_tail": "",
                   "iou_centered": 0.0, "iou_raw": 0.0,
                   "reply_tail": reply_tail}
        if code is None:
            return d
        res = exec_code(tag, code, cand_dir)   # writes cand_dir/<tag>.py/.stl
        d.update({k: res[k] for k in ("exec_ok", "exec_rc", "stderr_tail")})
        if d["exec_ok"]:
            pair = iou_pair(os.path.join(cand_dir, f"{tag}.stl"),
                            os.path.join(gt_dir, f"{key}.stl"))
            d["iou_centered"] = pair["iou_centered"]
            d["iou_raw"] = pair["iou_raw"]
            d["mesh_ok"] = pair["mesh_ok"]
        return d

    # ---- all k draws for every sample (no early stop) ----
    for draw in range(args.k):
        print(f"[exp1] draw {draw} ({'greedy' if draw == 0 else 'sampled'}): "
              f"generating {len(samples)}", flush=True)
        outs = []
        for b in range(0, len(samples), args.batch):
            chunk = samples[b:b + args.batch]
            msgs = [build_gen_messages(s["image"], cfg) for s in chunk]
            outs.extend(gen_batch(msgs, sample_mode=(draw > 0)))
            print(f"[exp1]   gen d{draw}: {min(b + args.batch, len(samples))}"
                  f"/{len(samples)}", flush=True)
        n_deg = sum("!!!!!!!!" in t for t in outs)
        if n_deg > max(4, len(outs) // 3):
            raise RuntimeError(f"{n_deg} degenerate generations — bad GPU?")

        def run_one(i_text):
            i, text = i_text
            code = extract_code(text)
            tail = (code and f"```python\n{code}\n```") or text[-1200:]
            d = exec_and_score(recs[i]["key"],
                               f"{recs[i]['key']}_d{draw}", code, tail)
            d["draw"] = draw
            recs[i]["draws"].append(d)
        list(pool_ex.map(run_one, enumerate(outs)))
        ok = sum(r["draws"][-1]["exec_ok"] for r in recs)
        print(f"[exp1] draw {draw}: {ok}/{len(recs)} executed", flush=True)
        # incremental save (draws so far)
        _dump(args, recs, partial=True)

    # ---- one greedy repair round where NO draw executed (deployed policy) ----
    todo = [i for i, r in enumerate(recs)
            if not any(d["exec_ok"] for d in r["draws"])]
    if todo:
        print(f"[exp1] repair round: {len(todo)} samples", flush=True)
        msgs = []
        for i in todo:
            last = recs[i]["draws"][-1]
            rec_like = {"code": last["code"], "exec_rc": last["exec_rc"],
                        "stderr_tail": last["stderr_tail"]}
            msgs.append(build_repair_messages(
                samples[i]["image"], cfg, last["reply_tail"],
                feedback_text(rec_like)))
        outs = []
        for b in range(0, len(msgs), args.batch):
            outs.extend(gen_batch(msgs[b:b + args.batch], sample_mode=False))

        def rep_one(j_text):
            j, text = j_text
            i = todo[j]
            code = extract_code(text)
            tail = (code and f"```python\n{code}\n```") or text[-1200:]
            recs[i]["repair"] = exec_and_score(
                recs[i]["key"], f"{recs[i]['key']}_rep", code, tail)
        list(pool_ex.map(rep_one, enumerate(outs)))

    # reply tails only matter for repair prompting; drop from the record
    for r in recs:
        for d in r["draws"]:
            d.pop("reply_tail", None)
        if r["repair"]:
            r["repair"].pop("reply_tail", None)

    _dump(args, recs, partial=False)
    print("[exp1] done", flush=True)


def policies(rec: dict) -> dict:
    """The three policies over one sample's draws (+ repair fallback)."""
    draws = sorted(rec["draws"], key=lambda d: d["draw"])
    execd = [d for d in draws if d["exec_ok"]]
    rep = rec.get("repair")
    rep_iou = rep["iou_centered"] if rep and rep["exec_ok"] else 0.0

    if execd:
        first = min(execd, key=lambda d: d["draw"])
        deployed, deployed_by = first["iou_centered"], first["draw"]
        best = max(execd, key=lambda d: d["iou_centered"])
        oracle, oracle_draw = best["iou_centered"], best["draw"]
    else:
        deployed, deployed_by = rep_iou, ("repair" if rep_iou else None)
        oracle, oracle_draw = rep_iou, ("repair" if rep_iou else None)

    d0 = next((d for d in draws if d["draw"] == 0), None)
    greedy = d0["iou_centered"] if d0 and d0["exec_ok"] else 0.0
    return {"deployed_iou": deployed, "deployed_by": deployed_by,
            "oracle_iou": oracle, "oracle_draw": oracle_draw,
            "greedy_iou": greedy, "n_exec": len(execd)}


def _dump(args, recs, partial: bool):
    out = {"config": {"ckpt": args.ckpt, "run": args.run, "n": args.n,
                      "k": args.k, "temperature": args.temperature,
                      "worker": args.worker, "stride": args.stride,
                      "partial": partial},
           "records": recs}
    if not partial:
        pols = [policies(r) for r in recs]
        n = len(recs)
        out["metrics"] = {
            "n": n,
            "deployed_mean": sum(p["deployed_iou"] for p in pols) / n,
            "oracle_mean": sum(p["oracle_iou"] for p in pols) / n,
            "greedy_mean": sum(p["greedy_iou"] for p in pols) / n,
            "deployed_exec_frac": sum(
                1 for p in pols if p["deployed_by"] is not None) / n,
            "coverage_by_draw": {str(k): v for k, v in sorted(Counter(
                str(p["deployed_by"]) for p in pols).items())},
            "oracle_win_draw": {str(k): v for k, v in sorted(Counter(
                str(p["oracle_draw"]) for p in pols).items())},
        }
        print(json.dumps(out["metrics"], indent=1), flush=True)
    name = ("bo4_oracle.json" if args.stride == 1
            else f"bo4_oracle_w{args.worker:02d}.json")
    path = os.path.join(args.out, name)
    with open(path + ".tmp", "w") as f:
        json.dump(out, f, indent=1)
    os.replace(path + ".tmp", path)


if __name__ == "__main__":
    main()
