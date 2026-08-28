"""VLM critic: drawing PNG + per-candidate 3-view renders -> pick best / flag gross.

    python3 vlm_critic.py [--model "claude-moonshotai/Kimi-K3[1m]"] [--workers 8]
                          [--tag kimi] [--keys k1,k2]

One call per sample. Candidates are letter-labeled in a key-seeded shuffled order
(position-bias control). Output artifacts/vlm_<tag>.json: raw replies + parsed
verdicts + derived policy picks (vlm-pick / vlm-argmax / vlm-gate).
Selection-time inputs only (drawing + candidate renders); no GT, no IoU.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import pickle
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bo4data  # noqa: E402

ROUTER = os.environ.get("KING_ROUTER", "http://wpk-serv-07.mechse.illinois.edu:3456")
RENDERS = "/srv/scratch/bimrose2/drawing_agent_exp3/renders"
CACHE = "/srv/scratch/bimrose2/drawing_agent_exp1/wds_dataset/eval_cache_v15.pkl"
LETTERS = "ABCD"


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

SYSTEM = """You are an expert mechanical-drawing inspector. You will see (1) a dimensioned multi-view engineering drawing of a part (the specification; dimensions in mm, blue ink) and (2) several CANDIDATE reconstructions, each shown as labeled orthographic line renders (TOP / FRONT / RIGHT, same view conventions as the drawing; renders carry no dimensions).

Judge how well each candidate matches the drawing:
- Overall proportions per view against the drawing's dimension chains (compute overall extents from the dimension text; a chain of segment dims sums to the overall).
- Presence, size and position of features: steps, notches, slots, holes, bosses, ribs, hollows.
- Gross errors matter most: wrong overall shape, missing/extra major features, badly wrong proportions. Ignore tiny fillet/chamfer differences and line-style differences.

Reply with a short per-candidate assessment (one line each), then EXACTLY one JSON object on the final line:
{"scores": {"A": 0-10, ...}, "best": "<letter>", "gross": ["<letters that are grossly wrong>"]}
Scores: 10 = matches every dimensioned feature; 7-9 minor deviations; 4-6 clear feature/size errors; 0-3 grossly wrong. "best" must be one of the candidate letters. "gross" may be empty."""


def img_block(data: bytes):
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                        "data": base64.b64encode(data).decode()}}


def call_model(model, messages, max_tokens=6000, temperature=0.0, tag=""):
    body = {"model": model, "max_tokens": max_tokens, "temperature": temperature,
            "system": SYSTEM, "messages": messages}
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
            payload = e.read().decode(errors="replace")[:300]
            last = f"HTTP {e.code}: {payload}"
            if e.code in (400, 401, 403, 404, 413):
                raise RuntimeError(f"{tag} non-retryable {last}")
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{tag} failed after retries: {last}")


def parse_verdict(text, letters):
    m = None
    for m in re.finditer(r"\{[^{}]*\{[^{}]*\}[^{}]*\}", text or ""):
        pass
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        scores = {k: float(v) for k, v in d.get("scores", {}).items() if k in letters}
        best = d.get("best")
        gross = [g for g in d.get("gross", []) if g in letters]
        if best not in letters and scores:
            best = max(scores, key=scores.get)
        if best not in letters:
            return None
        return {"scores": scores, "best": best, "gross": gross}
    except Exception:  # noqa: BLE001
        return None


def judge_sample(rec, drawing_png, model):
    key = rec["key"]
    ex = [d["draw"] for d in bo4data.exec_draws(rec)]
    have = [(i, os.path.join(RENDERS, f"{rec['draws'][i]['tag']}.png"))
            for i in ex]
    have = [(i, p) for i, p in have if os.path.exists(p) and os.path.getsize(p) > 0]
    if len(have) < 2:
        return {"key": key, "skipped": f"only {len(have)} rendered candidates"}
    order = list(range(len(have)))
    random.Random(key).shuffle(order)
    letter_of = {}   # draw idx -> letter
    blocks = [img_block(drawing_png),
              {"type": "text", "text": "Above: the engineering drawing (the specification)."}]
    for pos, oi in enumerate(order):
        draw_idx, png = have[oi]
        letter = LETTERS[pos]
        letter_of[draw_idx] = letter
        with open(png, "rb") as f:
            blocks.append(img_block(f.read()))
        blocks.append({"type": "text", "text": f"Candidate {letter}."})
    blocks.append({"type": "text", "text":
                   f"Assess candidates {', '.join(letter_of[i] for i, _ in have)} "
                   "against the drawing and finish with the JSON verdict line."})
    t0 = time.time()
    text, usage = call_model(model, [{"role": "user", "content": blocks}], tag=key)
    verdict = parse_verdict(text, set(letter_of.values()))
    return {"key": key, "letter_of": {str(k): v for k, v in letter_of.items()},
            "reply": text, "usage": usage, "t_s": round(time.time() - t0, 1),
            "verdict": verdict}


def derive_policies(recs, results):
    """verdict -> picks for vlm-pick / vlm-argmax / vlm-gate."""
    picks = {"vlm-pick": {}, "vlm-argmax": {}, "vlm-gate": {}}
    for r in recs:
        key = r["key"]
        first = bo4data.first_exec_draw(r)
        res = results.get(key, {})
        v = res.get("verdict")
        for p in picks:
            picks[p][key] = first
        if not v:
            continue
        letter_of = {int(k): l for k, l in res["letter_of"].items()}
        of_letter = {l: k for k, l in letter_of.items()}
        if v["best"] in of_letter:
            picks["vlm-pick"][key] = of_letter[v["best"]]
        if v["scores"]:
            mx = max(v["scores"].values())
            tied = sorted(of_letter[l] for l, s in v["scores"].items()
                          if s == mx and l in of_letter)
            if tied:
                picks["vlm-argmax"][key] = first if first in tied else tied[0]
        # gate: keep first unless VLM says first is gross or scores it far below max
        fl = letter_of.get(first)
        s = v["scores"]
        gross_first = (fl in v["gross"]) or (fl in s and s and
                                             s[fl] <= max(s.values()) - 3)
        if gross_first:
            good = [of_letter[l] for l in s
                    if l not in v["gross"] and l in of_letter]
            if v["best"] in of_letter and of_letter[v["best"]] != first:
                picks["vlm-gate"][key] = of_letter[v["best"]]
            elif good:
                picks["vlm-gate"][key] = min(good)
    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-moonshotai/Kimi-K3[1m]")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tag", default="kimi")
    ap.add_argument("--keys", default=None)
    args = ap.parse_args()

    recs = bo4data.load_records()
    if args.keys:
        want = args.keys.split(",")
        recs = [r for r in recs if any(r["key"].startswith(w) for w in want)]
    with open(CACHE, "rb") as f:
        samples = pickle.load(f)["samples"]

    t0 = time.time()
    results = {}
    n_calls = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(judge_sample, r, samples[r["key"]]["png"], args.model):
                r["key"] for r in recs}
        for fut in as_completed(futs):
            key = futs[fut]
            try:
                res = fut.result()
            except Exception as e:  # noqa: BLE001
                res = {"key": key, "error": repr(e)[:300]}
            results[key] = res
            if "usage" in res:
                n_calls += 1
            ok = "ok" if res.get("verdict") else res.get("skipped") or res.get("error", "PARSE-FAIL")
            print(f"[{len(results)}/{len(recs)}] {key[:8]} {ok if ok != 'ok' else 'ok'}",
                  flush=True)
    wall = time.time() - t0

    all_recs = bo4data.load_records()
    picks = derive_policies(all_recs, results)
    out = {"model": args.model, "n_calls": n_calls, "wall_s": round(wall, 1),
           "n_verdicts": sum(1 for r in results.values() if r.get("verdict")),
           "policies": picks, "results": results}
    os.makedirs(os.path.join(HERE, "artifacts"), exist_ok=True)
    path = os.path.join(HERE, "artifacts", f"vlm_{args.tag}.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"verdicts {out['n_verdicts']}/{len(recs)}  calls {n_calls}  wall {wall:.0f}s")
    print("wrote", path)


if __name__ == "__main__":
    main()
