"""Exp2 driver: single-shot vs agentic arms, same model (Kimi K3 via hub router),
same drawings, same base prompt.

Design: the turn-1 completion IS the single-shot arm (scored as-is) and seeds the
agentic loop, so the measured delta isolates the loop rather than sampling noise.
The loop feedback contains ONLY measurements of the model's own candidate (exec
result, bbox/volume/face counts, orthographic re-render) — never GT values, never
PASS/FAIL verdicts (cadgenbench PASS-tool trap).

Run under any python3.9+ (network only; all heavy work in subprocesses):

    python3 harness/run_arms.py [--parts uid1,uid2] [--workers 5]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
PY = "/software/python-3.11.1/bin/python3.11"
EXEC_HARNESS = os.path.join(HERE, "exec_harness.py")
INSPECT = os.path.join(HERE, "inspect_candidate.py")
IOU = os.path.join(HERE, "iou.py")
RUNS = os.path.join(EXP, "artifacts", "runs")
TRAJ = os.path.join(EXP, "trajectories")

ROUTER = os.environ.get("KING_ROUTER", "http://wpk-serv-07.mechse.illinois.edu:3456")
MODEL = "claude-moonshotai/Kimi-K3[1m]"   # overridden by --model
MAX_CALLS = 12           # total model calls per part (1 single-shot + <=11 loop)
TEMPERATURE = 0.6
MAX_TOKENS = 8000

_print_lock = threading.Lock()


def log(*a):
    with _print_lock:
        print(*a, flush=True)


def _api_key():
    k = os.environ.get("KING_API_KEY")
    if k:
        return k
    with open(os.path.expanduser("~/.claude-hub/keys.json")) as f:
        keys = json.load(f)["keys"]
    for key, meta in keys.items():
        if not meta.get("revoked") and meta.get("name") == "miles":
            return key
    raise RuntimeError("no usable hub key")


KEY = _api_key()

SYSTEM_PROMPT = """You are an expert mechanical design engineer. You reconstruct exact CAD solid models from dimensioned multi-view engineering drawings by writing Python code for build123d (version 0.10).

READING THE DRAWING (do this carefully before writing any code):
1. Identify the views by their printed labels (Top, Front, Right, ISO). Projection is orthographic: Top shows the XY plane seen from +Z (X right, Y up on the sheet); Front shows XZ seen from -Y (X right, Z up); Right shows YZ seen from +X (Y right, Z up). The ISO view shows overall form only and carries no dimensions.
2. For every axis of every view, classify each linear dimension as an OVERALL (total extent of the part) or a COMPONENT (one segment of a chain). Note which two feature edges each dimension's extension lines touch.
3. Some drawings give NO overall dimension on an axis — only a chain of component dimensions. Then write out the arithmetic chain and SUM the segments to get the overall extent (e.g. 28 + 21 + 17 = 66). Never eyeball an overall that a chain determines exactly.
4. Cross-check every extent against the other views (the same axis usually appears in two views) and against the ISO view's proportions.
5. Hole callouts: "2X ⌀ 8 THRU" means two through-holes of diameter 8 mm. Read hole positions from where the circles sit in the views; use symmetry when it is evident. Dashed gray lines are hidden edges revealing internal features.

WRITING THE CODE:
- Start with a named-parameter block: every dimension read off the drawing becomes a named variable with a `# mm` comment. Compute derived values by formula from those variables (e.g. W = w1 + w2 + w3). Never inline unexplained numbers.
- Priorities, strictly in order: exact absolute sizes; then the complete feature set (steps, notches, slots, holes, bosses); then overall form; fillets/chamfers last (omit them unless dimensioned).
- Prefer simple robust constructions: Box / Cylinder with align=..., Locations(...), Mode.SUBTRACT inside a single BuildPart.
- All units are mm. The part's position relative to the origin does not matter, but its ORIENTATION must follow the views (Top = XY plane, etc.).
- The script must bind the finished solid to a variable `part` and end with:
  export_step(part, "output.step")

OUTPUT FORMAT (always exactly this):
<plan>
Concise reading of each view; the dimension chain per axis with explicit arithmetic; the feature list with sizes and positions.
</plan>
```python
# one complete runnable script
```"""

TASK_TEXT = ("Reconstruct the part shown in this engineering drawing as a build123d "
             "script. All dimensions are in mm. Follow the output format exactly.")

FEEDBACK_OK = """Your script executed. Measurements of the solid YOUR script produced:
- solids: {n_solids}; mesh watertight: {watertight}
- bounding box X × Y × Z: {bx} × {by} × {bz} mm
- volume: {vol} mm³
- faces: {n_faces} total ({n_plane} planar, {n_cyl} cylindrical); cylindrical radii: {radii} mm
Attached: orthographic line renders (Top / Front / Right) of YOUR current solid, same view conventions as the drawing.
Compare them against the original drawing yourself: per-axis extents vs the dimension chains, presence/size/position of every feature, hole diameters.
If a revision is needed, reply in the same format (<plan> then one complete ```python script). If the current solid already matches the drawing exactly, reply with the single word FINAL."""

FEEDBACK_OK_NORENDER = FEEDBACK_OK.replace(
    "Attached: orthographic line renders (Top / Front / Right) of YOUR current solid, same view conventions as the drawing.\n",
    "(No render available for this candidate.)\n")

FEEDBACK_FAIL = """Your script failed to execute.
--- stderr (tail) ---
{stderr}
Reply with a corrected <plan> (if your reading changed) and one complete ```python script."""

FEEDBACK_NOCODE = ("Your previous reply contained no ```python code block. Reply with "
                   "<plan> and one complete ```python script that exports output.step.")


# ---------------------------------------------------------------------------
# Router client

def call_model(system, messages, tag=""):
    body = {"model": MODEL, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE,
            "system": system, "messages": messages}
    data = json.dumps(body).encode()
    last = None
    for attempt in range(4):
        req = urllib.request.Request(
            f"{ROUTER}/v1/messages", data=data,
            headers={"content-type": "application/json", "x-api-key": KEY,
                     "anthropic-version": "2023-06-01", "x-hub-user": "bimrose2"})
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                resp = json.loads(r.read())
            text = "".join(c.get("text", "") for c in resp.get("content", [])
                           if c.get("type") == "text")
            return text, resp.get("usage", {})
        except urllib.error.HTTPError as e:
            payload = e.read().decode(errors="replace")[:500]
            last = f"HTTP {e.code}: {payload}"
            if e.code in (400, 401, 403, 404, 413):
                raise RuntimeError(f"{tag} non-retryable {last}")
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{tag} model call failed after retries: {last}")


def img_block(path):
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return {"type": "image", "source": {"type": "base64",
                                        "media_type": "image/png", "data": data}}


def build_payload(turns):
    """turns: [{'role', 'text', 'image': path|None, 'prunable': bool}] ->
    anthropic messages. All prunable images except the LAST one are replaced by a
    text stub (keeps <=2 images per prompt: the drawing + newest render)."""
    last_prunable = max((i for i, t in enumerate(turns)
                         if t.get("image") and t.get("prunable")), default=None)
    msgs = []
    for i, t in enumerate(turns):
        blocks = []
        if t.get("image"):
            if t.get("prunable") and i != last_prunable:
                blocks.append({"type": "text",
                               "text": "[render of an earlier candidate omitted]"})
            else:
                blocks.append(img_block(t["image"]))
        blocks.append({"type": "text", "text": t["text"]})
        msgs.append({"role": t["role"], "content": blocks})
    return msgs


# ---------------------------------------------------------------------------
# Candidate handling

CODE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(text):
    blocks = CODE_RE.findall(text or "")
    return blocks[-1].strip() + "\n" if blocks else None


def extract_plan(text):
    m = re.search(r"<plan>(.*?)</plan>", text or "", re.DOTALL)
    return m.group(1).strip() if m else None


def is_final(text):
    return extract_code(text) is None and re.search(r"\bFINAL\b", text or "")


def exec_candidate(code, rundir, k):
    code_path = os.path.join(rundir, f"cand_{k:02d}.py")
    stl = os.path.join(rundir, f"cand_{k:02d}.stl")
    step = os.path.join(rundir, f"cand_{k:02d}.step")
    with open(code_path, "w") as f:
        f.write(code)
    try:
        r = subprocess.run([PY, EXEC_HARNESS, code_path, stl, step],
                           capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        return {"ok": False, "stderr": "execution timed out after 240 s", "rc": -1}
    if r.returncode != 0 or not os.path.exists(stl):
        return {"ok": False, "stderr": (r.stderr or "")[-1500:], "rc": r.returncode}
    return {"ok": True, "stl": stl, "step": step, "rc": 0}


def inspect_candidate(step, stl, rundir, k):
    png = os.path.join(rundir, f"cand_{k:02d}.render.png")
    mjson = os.path.join(rundir, f"cand_{k:02d}.meas.json")
    try:
        subprocess.run([PY, INSPECT, step, stl, png, mjson],
                       capture_output=True, text=True, timeout=240)
        with open(mjson) as f:
            meas = json.load(f)
    except Exception:  # noqa: BLE001
        return None, None
    return meas, (png if meas.get("render_ok") else None)


def score(pred_stl, gt_stl):
    if not pred_stl:
        return {"mesh_ok": False, "iou_raw": 0.0, "iou_centered": 0.0}
    try:
        r = subprocess.run([PY, IOU, pred_stl, gt_stl],
                           capture_output=True, text=True, timeout=300)
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return {"mesh_ok": False, "iou_raw": 0.0, "iou_centered": 0.0}


def feedback_text(res, meas, have_render):
    if not res["ok"]:
        return FEEDBACK_FAIL.format(stderr=res.get("stderr", "")[-1200:])
    if meas is None:
        return FEEDBACK_OK_NORENDER.format(
            n_solids="?", watertight="?", bx="?", by="?", bz="?", vol="?",
            n_faces="?", n_plane="?", n_cyl="?", radii="?")
    bx, by, bz = meas.get("bbox_mm", ["?", "?", "?"])
    tmpl = FEEDBACK_OK if have_render else FEEDBACK_OK_NORENDER
    return tmpl.format(
        n_solids=meas.get("n_solids", meas.get("n_mesh_components", "?")),
        watertight=meas.get("watertight", "?"), bx=bx, by=by, bz=bz,
        vol=meas.get("volume_mm3", "?"), n_faces=meas.get("n_faces", "?"),
        n_plane=meas.get("n_planar_faces", "?"),
        n_cyl=meas.get("n_cylindrical_faces", "?"),
        radii=meas.get("cylindrical_radii_mm", "?"))


# ---------------------------------------------------------------------------

def run_part(rec):
    uid = rec["uid"]
    rundir = os.path.join(RUNS, uid)
    os.makedirs(rundir, exist_ok=True)
    gt_stl = os.path.join(EXP, rec["gt_stl"])
    drawing = os.path.join(EXP, rec["png"])

    turns = [{"role": "user", "text": TASK_TEXT, "image": drawing,
              "prunable": False}]
    record = {"uid": uid, "split": rec["split"], "family": rec["family"],
              "model": MODEL, "temperature": TEMPERATURE, "turns": []}
    candidates = []          # (k, code, res)
    t_start = time.time()
    t_singleshot = None
    ss_stl = None
    n_calls = 0
    nocode_streak = 0
    stop_reason = "budget"

    while n_calls < MAX_CALLS:
        n_calls += 1
        t0 = time.time()
        text, usage = call_model(SYSTEM_PROMPT, build_payload(turns), tag=uid)
        t_call = time.time() - t0
        turns.append({"role": "assistant", "text": text, "image": None})
        code = extract_code(text)
        entry = {"turn": n_calls, "t_call_s": round(t_call, 1), "usage": usage,
                 "plan": extract_plan(text), "text": text}
        if code is None:
            if is_final(text):
                entry["action"] = "FINAL"
                record["turns"].append(entry)
                stop_reason = "final"
                if n_calls == 1:  # degenerate: FINAL with no code on turn 1
                    t_singleshot = time.time() - t_start
                break
            nocode_streak += 1
            entry["action"] = "no_code"
            record["turns"].append(entry)
            if n_calls == 1:
                t_singleshot = time.time() - t_start
            if nocode_streak >= 3:
                stop_reason = "no_code"
                break
            turns.append({"role": "user", "text": FEEDBACK_NOCODE, "image": None})
            continue
        nocode_streak = 0
        k = len(candidates) + 1
        res = exec_candidate(code, rundir, k)
        entry["action"] = "candidate"
        entry["cand"] = k
        entry["exec_ok"] = res["ok"]
        candidates.append((k, code, res))
        if n_calls == 1:
            t_singleshot = time.time() - t_start
            if res["ok"]:
                ss_stl = res["stl"]
        meas = png = None
        if res["ok"]:
            meas, png = inspect_candidate(res["step"], res["stl"], rundir, k)
            entry["meas"] = meas
        record["turns"].append(entry)
        if n_calls >= MAX_CALLS:
            break
        turns.append({"role": "user",
                      "text": feedback_text(res, meas, png is not None),
                      "image": png, "prunable": True})

    t_agentic = time.time() - t_start

    # Final candidate = last successfully-executing script (checkpoint-first).
    final_k = final_stl = None
    for k, code, res in reversed(candidates):
        if res["ok"]:
            final_k, final_stl = k, res["stl"]
            break

    ss_score = score(ss_stl, gt_stl)
    ag_score = score(final_stl, gt_stl)
    per_cand = {}
    for k, code, res in candidates:
        if res["ok"]:
            per_cand[k] = score(res["stl"], gt_stl)
    best_k = max(per_cand, key=lambda k: per_cand[k]["iou_centered"], default=None)

    summary = {
        "uid": uid, "split": rec["split"], "family": rec["family"],
        "ss_exec_ok": ss_stl is not None,
        "ss_iou": round(ss_score["iou_centered"], 4),
        "ag_exec_ok": final_stl is not None,
        "ag_iou": round(ag_score["iou_centered"], 4),
        "ag_final_cand": final_k,
        "best_iou": round(per_cand[best_k]["iou_centered"], 4) if best_k else 0.0,
        "best_cand": best_k,
        "n_calls": n_calls, "n_candidates": len(candidates),
        "stop_reason": stop_reason,
        "t_singleshot_s": round(t_singleshot or 0.0, 1),
        "t_agentic_s": round(t_agentic, 1),
    }
    record["summary"] = summary
    record["per_candidate_iou"] = {str(k): round(v["iou_centered"], 4)
                                   for k, v in per_cand.items()}
    os.makedirs(TRAJ, exist_ok=True)
    with open(os.path.join(TRAJ, f"{uid}.json"), "w") as f:
        json.dump(record, f, indent=1)

    # Accepted trajectory (STaR-style gate): agentic final with IoU >= 0.8.
    if final_k is not None and ag_score["iou_centered"] >= 0.8:
        acc = os.path.join(TRAJ, "accepted")
        os.makedirs(acc, exist_ok=True)
        final_code = next(c for k, c, r in candidates if k == final_k)
        plans = [e["plan"] for e in record["turns"] if e.get("plan")]
        with open(os.path.join(acc, f"{uid}.py"), "w") as f:
            f.write(f"# {uid} — agentic final (cand {final_k}), "
                    f"IoU {ag_score['iou_centered']:.3f}\n" + final_code)
        with open(os.path.join(acc, f"{uid}.plan.md"), "w") as f:
            f.write(f"# {uid} — accepted trajectory plan\n\n"
                    + "\n\n---\n\n".join(plans))

    log(f"[{uid}] ss={summary['ss_iou']:.3f} ag={summary['ag_iou']:.3f} "
        f"best={summary['best_iou']:.3f} calls={n_calls} "
        f"stop={stop_reason} t_ss={summary['t_singleshot_s']}s "
        f"t_ag={summary['t_agentic_s']}s")
    return summary


def main():
    global MODEL, RUNS, TRAJ, MAX_TOKENS
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default=None, help="comma-separated uids")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    ap.add_argument("--tag", default=None,
                    help="secondary-run tag: writes runs/<tag>/, results_<tag>.json, "
                         "trajectories/<tag>/ (default: primary untagged layout)")
    args = ap.parse_args()
    MODEL = args.model
    MAX_TOKENS = args.max_tokens
    results_name = "results.json"
    if args.tag:
        RUNS = os.path.join(EXP, "artifacts", "runs", args.tag)
        TRAJ = os.path.join(EXP, "trajectories", args.tag)
        results_name = f"results_{args.tag}.json"

    with open(os.path.join(EXP, "artifacts", "manifest.json")) as f:
        manifest = json.load(f)
    if args.parts:
        want = set(args.parts.split(","))
        manifest = [m for m in manifest if m["uid"] in want]

    os.makedirs(RUNS, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_part, rec): rec["uid"] for rec in manifest}
        for fut in as_completed(futs):
            uid = futs[fut]
            try:
                results.append(fut.result())
            except Exception as e:  # noqa: BLE001
                log(f"[{uid}] FAILED: {e!r}")
                results.append({"uid": uid, "error": repr(e)})

    out = os.path.join(EXP, "artifacts", results_name)
    results.sort(key=lambda r: r.get("uid", ""))
    with open(out, "w") as f:
        json.dump(results, f, indent=1)
    log(f"\nwrote {out}")


if __name__ == "__main__":
    main()
