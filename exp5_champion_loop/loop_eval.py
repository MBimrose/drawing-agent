"""Exp 5 — the fine-tuned champion inside the measurement-feedback loop.

One arm: turn 1 is exp1's greedy draw 0 (the 0.787 baseline), then up to
--max-rounds feedback rounds per sample, sampled at --loop-temperature
(default T=0.7/top-p 0.95 = the deployed best-of-4 draw settings; T=0 greedy
rounds are degenerate — the champion regenerates byte-identical code from
identical feedback). Feedback contains ONLY measurements of the model's own
candidate:
  * exec failure  -> the vendored deployed-repair feedback (stderr tail),
  * exec success  -> bbox / volume / solid+face census / cylindrical radii,
                     optionally a Top/Front/Right line-render image of the
                     candidate (--render on|off), and an invitation to output a
                     corrected full script or reply FINAL.
No ground truth, no PASS/FAIL verdicts. Final answer = last executing candidate
(checkpoint-first); best-seen is recorded out-of-loop for keep-best analysis.

Sharding, generation and scoring mirror exp1's bo4_oracle_eval.py (same env,
same eval cache, same iou_pair). Run via run_node.sh (8 workers/node, stride 16).
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.environ.get(
    "DRAWING_VLM_TRAIN", "/srv/scratch/bimrose2/drawing_agent_exp1/train_v14")
sys.path.insert(0, TRAIN)
sys.path.insert(0, os.path.join(TRAIN, "geom"))

from data_v14 import EVAL_CACHE, EVAL_CACHE_V15, _decode_png  # noqa: E402
from geom_eval_worker import (  # noqa: E402
    build_gen_messages, classify_ckpt, extract_code, feedback_text,
    load_model, run_config,
)
from iou import iou_pair  # noqa: E402

SW_PY = "/software/python-3.11.1/bin/python3.11"   # cairosvg + build123d 0.10
EXEC_HARNESS = os.path.join(HERE, "exec_harness.py")
INSPECT = os.path.join(HERE, "inspect_candidate.py")

FEEDBACK_OK = """Your script executed successfully. Measurements of the solid YOUR script produced:
- solids: {n_solids}; mesh watertight: {watertight}
- bounding box X x Y x Z: {bx} x {by} x {bz} mm
- volume: {vol} mm^3
- faces: {n_faces} total ({n_plane} planar, {n_cyl} cylindrical); cylindrical radii: {radii} mm
{render_line}Now verify your solid against the DRAWING, from scratch — do not trust your earlier reading:
1. Re-read every dimension printed in the drawing. For each axis (X, Y, Z), write out the arithmetic that determines the TARGET overall extent (a single overall dimension, or a sum of chained segment dimensions). Then compare each target extent with the measured bounding box above.
2. Count the holes and other features the drawing shows and compare with the cylindrical-face radii and face counts above (a through-hole of diameter d appears as a cylindrical face of radius d/2).
3. Check feature positions and sizes the same way{render_clause}.
If ANY extent, feature, size or position disagrees with the drawing, output the complete corrected script as a single ```python code block ending with `export_step(part, "output.step")`. Only if every check passes, reply with the single word FINAL."""

RENDER_LINE = ("Attached: orthographic line renders (Top / Front / Right) of "
               "YOUR current solid, same view conventions as the drawing.\n")
NO_RENDER_LINE = ""
RENDER_CLAUSE = (", comparing the attached renders of your solid against the "
                 "drawing's views outline by outline")
RENDER_STUB = "[render of an earlier candidate omitted]"


def exec_candidate(env_py: str, code: str, cand_dir: str, tag: str) -> dict:
    """Write + run one candidate; keep .py/.stl/.step under cand_dir."""
    code_path = os.path.join(cand_dir, f"{tag}.py")
    stl = os.path.join(cand_dir, f"{tag}.stl")
    step = os.path.join(cand_dir, f"{tag}.step")
    with open(code_path, "w") as f:
        f.write(code)
    out = {"exec_ok": False, "exec_rc": None, "stderr_tail": ""}
    try:
        p = subprocess.run([env_py, EXEC_HARNESS, code_path, stl, step],
                           capture_output=True, text=True, timeout=120)
        out["exec_rc"] = p.returncode
        out["exec_ok"] = p.returncode == 0 and os.path.exists(stl)
        if not out["exec_ok"]:
            out["stderr_tail"] = (p.stderr or "")[-1200:]
            if p.returncode == 3:
                out["stderr_tail"] = out["stderr_tail"] or "no output.step produced"
    except subprocess.TimeoutExpired:
        out["exec_rc"] = -9
        out["stderr_tail"] = "timeout after 120s"
    return out


def inspect(cand_dir: str, tag: str) -> tuple[dict | None, str | None]:
    """Measurements + best-effort render of an executed candidate."""
    step = os.path.join(cand_dir, f"{tag}.step")
    stl = os.path.join(cand_dir, f"{tag}.stl")
    png = os.path.join(cand_dir, f"{tag}.render.png")
    mjson = os.path.join(cand_dir, f"{tag}.meas.json")
    try:
        subprocess.run([SW_PY, INSPECT, step, stl, png, mjson],
                       capture_output=True, text=True, timeout=240)
        with open(mjson) as f:
            meas = json.load(f)
    except Exception:  # noqa: BLE001
        return None, None
    return meas, (png if meas.get("render_ok") else None)


def ok_feedback_text(meas: dict | None, have_render: bool) -> str:
    m = meas or {}
    bbox = m.get("bbox_mm", ["?", "?", "?"])
    return FEEDBACK_OK.format(
        n_solids=m.get("n_solids", m.get("n_mesh_components", "?")),
        watertight=m.get("watertight", "?"),
        bx=bbox[0], by=bbox[1], bz=bbox[2],
        vol=m.get("volume_mm3", "?"),
        n_faces=m.get("n_faces", "?"),
        n_plane=m.get("n_planar_faces", "?"),
        n_cyl=m.get("n_cylindrical_faces", "?"),
        radii=m.get("cylindrical_radii_mm", "?"),
        render_line=RENDER_LINE if have_render else NO_RENDER_LINE,
        render_clause=RENDER_CLAUSE if have_render else "")


def is_final(text: str) -> bool:
    tail = text.rsplit("</think>", 1)[-1]
    return "FINAL" in tail and extract_code(text) is None


class Convo:
    """Message list for one sample. Assistant turns mirror the vendored
    build_repair_messages format (reasoning_content='', content=code fence or
    reply tail); at most ONE render image is live (the newest)."""

    def __init__(self, image, cfg):
        self.msgs = build_gen_messages(image, cfg)
        self._last_render_idx = None

    def add_assistant(self, reply_tail: str):
        self.msgs.append({"role": "assistant", "reasoning_content": "",
                          "content": [{"type": "text", "text": reply_tail}]})

    def add_feedback(self, text: str, render_png: str | None):
        content = []
        if render_png:
            if self._last_render_idx is not None:
                old = self.msgs[self._last_render_idx]
                old["content"] = [c for c in old["content"]
                                  if c.get("type") != "image"]
                old["content"].insert(0, {"type": "text", "text": RENDER_STUB})
            from PIL import Image
            content.append({"type": "image",
                            "image": Image.open(render_png).convert("RGB")})
            self._last_render_idx = len(self.msgs)
        content.append({"type": "text", "text": text})
        self.msgs.append({"role": "user", "content": content})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--n", type=int, default=96)
    ap.add_argument("--max-rounds", type=int, default=8,
                    help="feedback rounds after turn 1")
    ap.add_argument("--loop-temperature", type=float, default=0.7,
                    help="sampling T for rounds >=1 (0 = greedy). Turn 1 is "
                         "always greedy. Default matches the deployed "
                         "best-of-4 draw settings (T=0.7, top-p 0.95): pure "
                         "greedy loops are degenerate — the champion "
                         "regenerates byte-identical code from identical "
                         "feedback (seen in smoke).")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=2400)
    ap.add_argument("--render", choices=["on", "off"], default="on")
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--keys", default=None,
                    help="comma-separated key prefixes (smoke tests); "
                         "overrides worker/stride")
    ap.add_argument("--model-base", default=None)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cand_dir = os.path.join(args.out, "candidates")
    os.makedirs(cand_dir, exist_ok=True)

    cfg = run_config(args.run)
    if cfg is None:
        sys.exit(f"[exp5] no config for run {args.run}")
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
    if args.keys:
        want = [w for w in args.keys.split(",") if w]
        keys = [k for k in keys if any(k.startswith(w) for w in want)]
    else:
        keys = keys[args.worker::args.stride]
    samples = [{"uuid": k, "image": _decode_png(cache["samples"][k]["png"])}
               for k in keys]
    print(f"[exp5] w{args.worker}/{args.stride}: {len(samples)} samples, "
          f"pool={pool}, render={args.render}, T_loop={args.loop_temperature}, "
          f"max_rounds={args.max_rounds}", flush=True)

    if args.model_base:
        cfg["model_id"] = args.model_base
    kind = classify_ckpt(args.ckpt)
    if kind != "hf":
        sys.exit(f"[exp5] expected consolidated HF checkpoint, got {kind}")
    print(f"[exp5] loading {args.ckpt}", flush=True)
    model, processor = load_model(args.ckpt, kind, cfg)

    import torch
    from qwen_vl_utils import process_vision_info

    def gen_batch(msgs_list, sample_mode=False):
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
        if sample_mode and args.loop_temperature > 0:
            kw.update(do_sample=True, temperature=args.loop_temperature,
                      top_p=0.95)
        else:
            kw["do_sample"] = False
        with torch.no_grad():
            out = model.generate(**enc, **kw)
        gen = out[:, enc["input_ids"].shape[1]:]
        return processor.tokenizer.batch_decode(gen, skip_special_tokens=True)

    pool_ex = ThreadPoolExecutor(max_workers=8)
    env_py = sys.executable

    def score(key: str, tag: str) -> dict:
        pair = iou_pair(os.path.join(cand_dir, f"{tag}.stl"),
                        os.path.join(gt_dir, f"{key}.stl"))
        return {"iou_centered": pair["iou_centered"],
                "iou_raw": pair["iou_raw"], "mesh_ok": pair["mesh_ok"]}

    t_start = time.time()
    recs = [{"key": s["uuid"], "rounds": [], "stop_reason": None,
             "n_model_calls": 0} for s in samples]
    convos = [Convo(s["image"], cfg) for s in samples]
    active = list(range(len(samples)))
    last_code = [None] * len(samples)          # previous candidate code
    nocode_streak = [0] * len(samples)

    def dump(partial: bool):
        out = {"config": {"ckpt": args.ckpt, "run": args.run, "n": args.n,
                          "max_rounds": args.max_rounds,
                          "loop_temperature": args.loop_temperature,
                          "render": args.render, "worker": args.worker,
                          "stride": args.stride, "partial": partial,
                          "wall_s": round(time.time() - t_start, 1)},
               "records": [summarize(r) for r in recs]}
        name = ("loop.json" if args.stride == 1 and not args.keys
                else f"loop_w{args.worker:02d}.json")
        if args.keys:
            name = "loop_smoke.json"
        path = os.path.join(args.out, name)
        with open(path + ".tmp", "w") as f:
            json.dump(out, f, indent=1)
        os.replace(path + ".tmp", path)

    def summarize(rec: dict) -> dict:
        cands = [r for r in rec["rounds"] if r.get("action") == "candidate"]
        execd = [r for r in cands if r["exec_ok"]]
        r0 = next((r for r in cands if r["round"] == 0), None)
        final = execd[-1] if execd else None
        best = max(execd, key=lambda r: r["iou_centered"]) if execd else None
        rec["summary"] = {
            "greedy_iou": (r0["iou_centered"] if r0 and r0["exec_ok"] else 0.0),
            "greedy_exec_ok": bool(r0 and r0["exec_ok"]),
            "final_iou": final["iou_centered"] if final else 0.0,
            "final_round": final["round"] if final else None,
            "best_iou": best["iou_centered"] if best else 0.0,
            "best_round": best["round"] if best else None,
            "n_candidates": len(cands),
        }
        return rec

    # ---- round 0: greedy turn 1 (= exp1 draw 0) ----
    for rnd in range(args.max_rounds + 1):
        if not active:
            break
        t0 = time.time()
        outs = []
        for b in range(0, len(active), args.batch):
            chunk = active[b:b + args.batch]
            outs.extend(gen_batch([convos[i].msgs for i in chunk],
                                  sample_mode=(rnd > 0)))
        gen_s = time.time() - t0
        if rnd == 0:
            n_deg = sum("!!!!!!!!" in t for t in outs)
            if n_deg > max(2, len(outs) // 3):
                raise RuntimeError(f"{n_deg} degenerate generations — bad GPU?")

        # execute+score candidates in parallel threads
        entries: dict[int, dict] = {}

        def handle(i_text):
            i, text = i_text
            rec = recs[i]
            rec["n_model_calls"] += 1
            code = extract_code(text)
            tail = (code and f"```python\n{code}\n```") or text[-1200:]
            e = {"round": rnd, "gen_s": round(gen_s / max(len(outs), 1), 1),
                 "reply_tail": tail, "reply_len": len(text)}
            if code is None:
                e["action"] = "final" if is_final(text) else "no_code"
                entries[i] = e
                return
            e["action"] = "candidate"
            e["code"] = code
            tag = f"{rec['key']}_r{rnd}"
            e.update(exec_candidate(env_py, code, cand_dir, tag))
            if e["exec_ok"]:
                e.update(score(rec["key"], tag))
                meas, png = inspect(cand_dir, tag)
                e["meas"] = meas
                e["render_ok"] = png is not None
                e["render_png"] = png
            else:
                e.update({"iou_centered": 0.0, "iou_raw": 0.0})
            entries[i] = e

        list(pool_ex.map(handle, zip(active, outs)))

        # bookkeeping + next-turn feedback
        still = []
        for i in active:
            e = entries[i]
            rec = recs[i]
            act = e["action"]
            if act == "final":
                rec["rounds"].append(_strip(e))
                rec["stop_reason"] = "final"
                continue
            if act == "no_code":
                nocode_streak[i] += 1
                rec["rounds"].append(_strip(e))
                if nocode_streak[i] >= 2:
                    rec["stop_reason"] = "no_code"
                    continue
                if rnd == args.max_rounds:
                    rec["stop_reason"] = "budget"
                    continue
                convos[i].add_assistant(e["reply_tail"])
                convos[i].add_feedback(feedback_text({"code": None}), None)
                still.append(i)
                continue
            nocode_streak[i] = 0
            # Convergence stop ONLY for an executing candidate: re-emitting a
            # WORKING script twice = the model's answer. Re-emitting a BROKEN
            # script is not a stop — each further round is a fresh T>0 sample
            # with a chance to deviate (the deployed bo4 policy gets 3 fresh
            # draws; cutting failed chains at round 1 would under-rescue).
            if (e["exec_ok"] and last_code[i] is not None
                    and e["code"].strip() == last_code[i]):
                rec["rounds"].append(_strip(e))
                rec["stop_reason"] = "converged"
                continue
            last_code[i] = e["code"].strip()
            rec["rounds"].append(_strip(e))
            if rnd == args.max_rounds:
                rec["stop_reason"] = "budget"
                continue
            convos[i].add_assistant(e["reply_tail"])
            if e["exec_ok"]:
                png = e.get("render_png") if args.render == "on" else None
                convos[i].add_feedback(
                    ok_feedback_text(e.get("meas"), png is not None), png)
            else:
                convos[i].add_feedback(feedback_text(
                    {"code": e["code"], "exec_rc": e["exec_rc"],
                     "stderr_tail": e["stderr_tail"]}), None)
            still.append(i)

        n_ok = sum(1 for i in entries
                   if entries[i].get("exec_ok"))
        print(f"[exp5] round {rnd}: {len(active)} active, {n_ok} executed, "
              f"{len(still)} continue ({gen_s:.0f}s gen)", flush=True)
        active = still
        dump(partial=True)

    dump(partial=False)
    means = [r["summary"] for r in recs]
    n = max(len(means), 1)
    print(f"[exp5] w{args.worker} done in {time.time()-t_start:.0f}s: "
          f"greedy {sum(m['greedy_iou'] for m in means)/n:.4f} -> "
          f"final {sum(m['final_iou'] for m in means)/n:.4f} "
          f"(best {sum(m['best_iou'] for m in means)/n:.4f})", flush=True)


def _strip(e: dict) -> dict:
    e = dict(e)
    if e.get("action") == "candidate":   # code is stored; tail is redundant
        e.pop("reply_tail", None)
    e.pop("render_png", None)
    return e


if __name__ == "__main__":
    main()
