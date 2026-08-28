"""Probe the lab's own direct vLLM endpoint (wpk-serv-07:8000/v1, internal
mechse host — see docs/context.md) per the exp6 plan: find which local lab key
it accepts, confirm it serves, and confirm it accepts image input.

Only ever talks to hosts in ALLOWED_HOSTS (lab-internal)."""
from __future__ import annotations

import base64
import glob
import json
import os
import sys
import urllib.request

ALLOWED_HOSTS = ("wpk-serv-07.mechse.illinois.edu",)
BASE = "http://wpk-serv-07.mechse.illinois.edu:8000/v1"
assert any(h in BASE for h in ALLOWED_HOSTS)


def req(path: str, key: str, body: dict | None = None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(
        BASE + path, data=data,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def main():
    keyfiles = [os.environ.get("SERVER7_API_KEY_FILE")] if \
        os.environ.get("SERVER7_API_KEY_FILE") else \
        sorted(glob.glob(os.path.expanduser("~/.claude-hub/*.key")))
    good = None
    for kf in keyfiles:
        key = open(kf).read().strip()
        try:
            models = req("/models", key, timeout=15)
            ids = [m.get("id") for m in models.get("data", [])]
            print(f"[probe] {os.path.basename(kf)}: OK /v1/models -> {ids}")
            good = (kf, key, ids)
            break
        except Exception as e:
            print(f"[probe] {os.path.basename(kf)}: {e}")
    if not good:
        print("[probe] NO usable key for the direct endpoint")
        return 1
    kf, key, ids = good
    model = ids[0] if ids else "moonshotai/Kimi-K3"

    # text-only completion sanity
    try:
        r = req("/chat/completions", key, {
            "model": model, "max_tokens": 30,
            "messages": [{"role": "user", "content": "Say READY and nothing else."}]})
        print(f"[probe] text completion OK: "
              f"{r['choices'][0]['message']['content']!r:.80}")
    except Exception as e:
        print(f"[probe] text completion FAILED: {e}")
        return 1

    # image input check (tiny 2x2 png)
    png = base64.b64encode(base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAD0lEQVQIHWP8//8/"
        b"AwwAgv4H/1L2n5EAAAAASUVORK5CYII=")).decode()
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], "rb") as f:
            png = base64.b64encode(f.read()).decode()
    try:
        r = req("/chat/completions", key, {
            "model": model, "max_tokens": 200,
            "messages": [{"role": "user", "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{png}"}},
                {"type": "text", "text": "Briefly, what is in this image?"}]}]},
            timeout=300)
        print(f"[probe] IMAGE completion OK: "
              f"{r['choices'][0]['message']['content'][:200]!r}")
        print(f"[probe] RESULT: direct endpoint usable, keyfile={kf}, model={model}")
    except Exception as e:
        print(f"[probe] IMAGE completion FAILED: {e}")
        print(f"[probe] RESULT: endpoint serves text but NOT images")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
