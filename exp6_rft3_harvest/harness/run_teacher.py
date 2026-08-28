"""Exp6 teacher driver: Kimi K3 + the exp4 FIXED agentic harness over the
rft_v2 train-pool reject batch.

Loop semantics are exp4's run_arms.py verbatim (12-call budget, measurement-only
feedback, no GT anywhere in the model's context, checkpoint-first final, FIXED
is_final: FINAL only counts in the last 300 chars of a <2000-char no-code
reply). Differences from exp4:
  * manifest = DATA/manifest.json (the 299-key pilot batch, GT STLs built
    locally by prep_gt.py);
  * two selectable backends -- "router" (hub anthropic-messages, exp4 path) and
    "direct" (vLLM openai chat completions at wpk-serv-07:8000/v1, keyfile
    ~/.claude-hub/serv08.key; images as data: URIs; assistant text =
    message.content, model reasoning stays in message.reasoning and is NOT fed
    back);
  * resume-safe append-only results jsonl (one line per finished part) +
    trajectory json per part under DATA/trajectories/<tag>/.

    python3 run_teacher.py --backend direct --workers 4 [--tag smoke --limit 5]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
DATA = "/srv/scratch/bimrose2/drawing_agent_exp6"
PY = "/software/python-3.11.1/bin/python3.11"
EXEC_HARNESS = os.path.join(HERE, "exec_harness.py")
INSPECT = os.path.join(HERE, "inspect_candidate.py")
IOU = os.path.join(HERE, "iou.py")

ROUTER = os.environ.get("KING_ROUTER", "http://wpk-serv-07.mechse.illinois.edu:3456")
ROUTER_MODEL = "claude-moonshotai/Kimi-K3[1m]"
DIRECT_BASE = "http://wpk-serv-07.mechse.illinois.edu:8000/v1"
DIRECT_MODEL = "moonshotai/Kimi-K3"
DIRECT_KEYFILE = os.path.expanduser("~/.claude-hub/serv08.key")

MAX_CALLS = 12
TEMPERATURE = 0.6
MAX_TOKENS = 16000

_print_lock = threading.Lock()


def log(*a):
    with _print_lock:
        print(*a, flush=True)


def _hub_key():
    k = os.environ.get("KING_API_KEY")
    if k:
        return k
    with open(os.path.expanduser("~/.claude-hub/keys.json")) as f:
        keys = json.load(f)["keys"]
    for key, meta in keys.items():
        if not meta.get("revoked") and meta.get("name") == "miles":
            return key
    raise RuntimeError("no usable hub key")


# --- prompts: exp4 verbatim ------------------------------------------------

SYSTEM_PROMPT = """You are an expert mechanical design engineer. You reconstruct exact CAD solid models from dimensioned multi-view engineering drawings by writing Python code for build123d (version 0.10).

READING THE DRAWING (do this carefully before writing any code):
1. The sheet shows unlabeled orthographic views in third-angle arrangement plus one pictorial view labeled "ISO VIEW (NTS)" (overall form only, not to scale, never dimensioned). Identify the orthographic views by position: the FRONT view sits below the TOP (plan) view, and the RIGHT side view sits to the right of the front view. Some sheets add a hatched SECTION view (labeled e.g. SECTION A-A, cut along the arrows marked on another view) revealing internal features. Coordinates: Top shows the XY plane seen from +Z (X right, Y up on the sheet); Front shows XZ seen from -Y (X right, Z up); Right shows YZ seen from +X (Y right, Z up). The title block and tolerance note carry no geometry.
2. For every axis of every view, classify each linear dimension as an OVERALL (total extent of the part) or a COMPONENT (one segment of a chain). Note which two feature edges each dimension's extension lines touch.
3. Some drawings give NO overall dimension on an axis — only a chain of component dimensions. Then write out the arithmetic chain and SUM the segments to get the overall extent (e.g. 28 + 21 + 17 = 66). Never eyeball an overall that a chain determines exactly.
4. Cross-check every extent against the other views (the same axis usually appears in two views) and against the ISO view's proportions.
5. Hole callouts use symbols: "4× ⌀5 THRU" = four through-holes of diameter 5 mm; "⌀30 ↓6" = diameter 30 hole 6 mm deep (blind); a countersink symbol (open V) with "⌀10 × 82°" = countersink to diameter 10 at 82° included angle; a counterbore symbol (⌴) with "⌀10 ↓4" = counterbore diameter 10, 4 mm deep. Read hole positions from where the circles sit in the views; use symmetry when it is evident. Dashed lines are hidden edges revealing internal features. "C1" on a corner = 45° chamfer of 1 mm; "R3" = fillet radius 3 mm. Include chamfers/fillets ONLY where such notes or dimensions call them out.

WRITING THE CODE:
- Start with a named-parameter block: every dimension read off the drawing becomes a named variable with a `# mm` comment. Compute derived values by formula from those variables (e.g. W = w1 + w2 + w3). Never inline unexplained numbers.
- Priorities, strictly in order: exact absolute sizes; then the complete feature set (steps, notches, slots, holes, bosses, pockets); then overall form; fillets/chamfers last (omit them unless dimensioned).
- Prefer simple robust constructions: Box / Cylinder with align=..., Locations(...), Mode.SUBTRACT inside a single BuildPart. CounterSinkHole / CounterBoreHole exist for callouts that need them.
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


# --- backends ---------------------------------------------------------------

class RouterBackend:
    name = "router"
    model = ROUTER_MODEL

    def __init__(self):
        self.key = _hub_key()

    def call(self, turns, tag=""):
        body = {"model": self.model, "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE, "system": SYSTEM_PROMPT,
                "messages": self._payload(turns)}
        data = json.dumps(body).encode()
        last = None
        for attempt in range(4):
            req = urllib.request.Request(
                f"{ROUTER}/v1/messages", data=data,
                headers={"content-type": "application/json", "x-api-key": self.key,
                         "anthropic-version": "2023-06-01",
                         "x-hub-user": "bimrose2"})
            try:
                with urllib.request.urlopen(req, timeout=1800) as r:
                    resp = json.loads(r.read())
                text = "".join(c.get("text", "") for c in resp.get("content", [])
                               if c.get("type") == "text")
                u = resp.get("usage", {})
                return text, {"in": u.get("input_tokens", 0) or 0,
                              "out": u.get("output_tokens", 0) or 0}
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"
                if e.code in (400, 401, 403, 404, 413):
                    raise RuntimeError(f"{tag} non-retryable {last}")
            except Exception as e:  # noqa: BLE001
                last = repr(e)
            time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"{tag} model call failed after retries: {last}")

    @staticmethod
    def _payload(turns):
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
                    with open(t["image"], "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    blocks.append({"type": "image",
                                   "source": {"type": "base64",
                                              "media_type": "image/png",
                                              "data": b64}})
            blocks.append({"type": "text", "text": t["text"]})
            msgs.append({"role": t["role"], "content": blocks})
        return msgs


class DirectBackend:
    name = "direct"
    model = DIRECT_MODEL

    def __init__(self):
        self.key = open(DIRECT_KEYFILE).read().strip()

    def call(self, turns, tag=""):
        body = {"model": self.model, "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE, "top_p": 0.95,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}]
                + self._payload(turns)}
        data = json.dumps(body).encode()
        last = None
        for attempt in range(4):
            req = urllib.request.Request(
                f"{DIRECT_BASE}/chat/completions", data=data,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {self.key}"})
            try:
                with urllib.request.urlopen(req, timeout=1800) as r:
                    resp = json.loads(r.read())
                msg = resp["choices"][0]["message"]
                text = msg.get("content") or ""
                u = resp.get("usage", {}) or {}
                return text, {"in": u.get("prompt_tokens", 0) or 0,
                              "out": u.get("completion_tokens", 0) or 0}
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"
                if e.code in (400, 401, 403, 404, 413):
                    raise RuntimeError(f"{tag} non-retryable {last}")
            except Exception as e:  # noqa: BLE001
                last = repr(e)
            time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"{tag} model call failed after retries: {last}")

    @staticmethod
    def _payload(turns):
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
                    with open(t["image"], "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    blocks.append({"type": "image_url",
                                   "image_url": {"url":
                                                 f"data:image/png;base64,{b64}"}})
            blocks.append({"type": "text", "text": t["text"]})
            msgs.append({"role": t["role"], "content": blocks})
        return msgs


# --- candidate handling: exp4 verbatim -------------------------------------

CODE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(text):
    blocks = CODE_RE.findall(text or "")
    return blocks[-1].strip() + "\n" if blocks else None


def extract_plan(text):
    m = re.search(r"<plan>(.*?)</plan>", text or "", re.DOTALL)
    return m.group(1).strip() if m else None


def is_final(text):
    """FIXED detector (exp4): FINAL counts only in the last 300 chars of a
    short (<2000 char) no-code reply — runaway thinking turns that mention
    FINAL mid-deliberation are NOT termination."""
    if extract_code(text) is not None:
        return False
    t = (text or "").strip()
    return len(t) < 2000 and re.search(r"\bFINAL\b", t[-300:])


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

def run_part(rec, backend, runs_root, traj_root):
    key = rec["key"]
    rundir = os.path.join(runs_root, key)
    os.makedirs(rundir, exist_ok=True)
    gt_stl = rec["gt_stl"]

    turns = [{"role": "user", "text": TASK_TEXT, "image": rec["png"],
              "prunable": False}]
    record = {"key": key, "backend": backend.name, "model": backend.model,
              "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
              "gen_iou": rec.get("gen_iou"), "turns": []}
    candidates = []
    t_start = time.time()
    ss_stl = None
    n_calls = 0
    nocode_streak = 0
    stop_reason = "budget"
    tok_in = tok_out = 0

    while n_calls < MAX_CALLS:
        n_calls += 1
        t0 = time.time()
        text, usage = backend.call(turns, tag=key)
        t_call = time.time() - t0
        tok_in += usage["in"]
        tok_out += usage["out"]
        turns.append({"role": "assistant", "text": text, "image": None})
        code = extract_code(text)
        entry = {"turn": n_calls, "t_call_s": round(t_call, 1), "usage": usage,
                 "plan": extract_plan(text), "text": text}
        if code is None:
            if is_final(text):
                entry["action"] = "FINAL"
                record["turns"].append(entry)
                stop_reason = "final"
                break
            nocode_streak += 1
            entry["action"] = "no_code"
            record["turns"].append(entry)
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
        if n_calls == 1 and res["ok"]:
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

    t_total = time.time() - t_start

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
        "key": key, "backend": backend.name,
        "gen_iou": rec.get("gen_iou"), "shard": rec.get("shard"),
        "ss_exec_ok": ss_stl is not None,
        "ss_iou": round(ss_score["iou_centered"], 4),
        "ag_exec_ok": final_stl is not None,
        "ag_iou": round(ag_score["iou_centered"], 4),
        "ag_final_cand": final_k,
        "best_iou": round(per_cand[best_k]["iou_centered"], 4) if best_k else 0.0,
        "best_cand": best_k,
        "n_calls": n_calls, "n_candidates": len(candidates),
        "stop_reason": stop_reason,
        "t_total_s": round(t_total, 1),
        "tokens": {"in": tok_in, "out": tok_out},
    }
    record["summary"] = summary
    record["per_candidate_iou"] = {str(k): round(v["iou_centered"], 4)
                                   for k, v in per_cand.items()}
    with open(os.path.join(traj_root, f"{key}.json"), "w") as f:
        json.dump(record, f, indent=1)

    log(f"[{key[:12]}] gen={rec.get('gen_iou', 0):.2f} ss={summary['ss_iou']:.3f} "
        f"ag={summary['ag_iou']:.3f} calls={n_calls} stop={stop_reason} "
        f"t={summary['t_total_s']:.0f}s tok={tok_in}/{tok_out}")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["router", "direct"], default="direct")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--parts", default=None, help="comma-separated key prefixes")
    ap.add_argument("--tag", default="main")
    args = ap.parse_args()

    backend = RouterBackend() if args.backend == "router" else DirectBackend()
    runs_root = os.path.join(DATA, "runs", args.tag)
    traj_root = os.path.join(DATA, "trajectories", args.tag)
    os.makedirs(runs_root, exist_ok=True)
    os.makedirs(traj_root, exist_ok=True)
    out = os.path.join(DATA, f"results_{args.tag}.jsonl")

    with open(os.path.join(DATA, "manifest.json")) as f:
        manifest = json.load(f)
    if args.limit:
        manifest = manifest[:args.limit]
    if args.parts:
        want = tuple(args.parts.split(","))
        manifest = [m for m in manifest if m["key"].startswith(want)]

    done = set()
    if os.path.exists(out):
        with open(out) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if "error" not in r:   # errored parts retry on next run
                        done.add(r["key"])
                except Exception:
                    pass
    manifest = [m for m in manifest if m["key"] not in done]
    log(f"[run tag={args.tag} backend={args.backend}] resume: {len(done)} done, "
        f"{len(manifest)} to run, workers={args.workers}")

    out_lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_part, rec, backend, runs_root, traj_root):
                rec["key"] for rec in manifest}
        for fut in as_completed(futs):
            key = futs[fut]
            try:
                summary = fut.result()
            except Exception as e:  # noqa: BLE001
                log(f"[{key[:12]}] FAILED: {e!r}")
                summary = {"key": key, "error": repr(e)}
            with out_lock, open(out, "a") as f:
                f.write(json.dumps(summary) + "\n")
    log(f"[run] wrote {out}")


if __name__ == "__main__":
    main()
