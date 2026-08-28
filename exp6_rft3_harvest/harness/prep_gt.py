"""Exp6 stage 4: extract drawing PNG + GT code for the pilot batch and build
GT STLs locally (execute GT code -> STEP -> STL via the exp4 exec harness,
/software/python-3.11.1 = build123d 0.10, same env the teacher candidates are
scored with). PNGs are composited RGBA-over-white exactly like data_v14's
_decode_png (what the generation pass fed the champion).

Keys whose GT fails to execute locally are dropped and logged
(DATA/gt_failures.json); the manifest (DATA/manifest.json) lists the survivors:
  [{key, shard, gen_iou, png, gt_stl}]

  python3 prep_gt.py [--jobs 16]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import tarfile
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = "/srv/scratch/bimrose2/drawing_agent_exp6"
TARS = os.path.join(DATA, "tars")
DRAW = os.path.join(DATA, "drawings")
GTC = os.path.join(DATA, "gt_code")
GTS = os.path.join(DATA, "gt_stl")
PY = "/software/python-3.11.1/bin/python3.11"
EXEC = os.path.join(HERE, "exec_harness.py")


def decode_png(b: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(b))
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=16)
    args = ap.parse_args()
    for d in (DRAW, GTC, GTS):
        os.makedirs(d, exist_ok=True)

    with open(os.path.join(DATA, "batch_pilot.json")) as f:
        batch = json.load(f)
    by_shard: dict[str, list[dict]] = {}
    for p in batch["parts"]:
        by_shard.setdefault(p["shard"], []).append(p)

    for shard, parts in sorted(by_shard.items()):
        want = {p["key"] for p in parts}
        with tarfile.open(os.path.join(TARS, shard)) as tf:
            for m in tf.getmembers():
                base, _, ext = m.name.partition(".")
                if base not in want:
                    continue
                data = tf.extractfile(m).read()
                if ext == "png":
                    decode_png(data).save(os.path.join(DRAW, base + ".png"))
                elif ext == "py":
                    with open(os.path.join(GTC, base + ".py"), "wb") as f:
                        f.write(data)
        print(f"[prep] {shard}: extracted {len(parts)} keys", flush=True)

    def build_gt(p: dict) -> tuple[dict, str | None]:
        key = p["key"]
        stl = os.path.join(GTS, key + ".stl")
        if os.path.exists(stl) and os.path.getsize(stl) > 0:
            return p, None
        cp = os.path.join(GTC, key + ".py")
        if not os.path.exists(cp):
            return p, "missing .py in shard"
        try:
            r = subprocess.run([PY, EXEC, cp, stl], capture_output=True,
                               text=True, timeout=240)
        except subprocess.TimeoutExpired:
            return p, "timeout 240s"
        if r.returncode != 0 or not os.path.exists(stl):
            return p, f"rc={r.returncode}: {(r.stderr or '')[-300:]}"
        return p, None

    ok, failures = [], {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for p, err in pool.map(build_gt, batch["parts"]):
            if err is None:
                q = dict(p)
                q["png"] = os.path.join(DRAW, p["key"] + ".png")
                q["gt_stl"] = os.path.join(GTS, p["key"] + ".stl")
                ok.append(q)
            else:
                failures[p["key"]] = err
                print(f"[prep] GT FAIL {p['key']}: {err[:120]}", flush=True)

    with open(os.path.join(DATA, "manifest.json"), "w") as f:
        json.dump(ok, f, indent=1)
    with open(os.path.join(DATA, "gt_failures.json"), "w") as f:
        json.dump(failures, f, indent=1)
    print(f"[prep] DONE: {len(ok)} usable, {len(failures)} GT failures "
          f"-> manifest.json", flush=True)


if __name__ == "__main__":
    main()
