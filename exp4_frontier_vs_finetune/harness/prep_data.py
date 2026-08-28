"""Extract the frozen 96-sample benchmark from eval_cache_v15.pkl.

Same pool selection as exp1/bo4_oracle_eval.py (and the champion's bestofn
eval): first 96 keys of pools["certified"] that have a GT mesh. Decodes each
drawing PNG (RGBA composited over white — data_v14._decode_png semantics) to
artifacts/drawings/<uuid>.png and writes artifacts/manifest.json.

    /software/python-3.11.1/bin/python3.11 harness/prep_data.py
"""
from __future__ import annotations

import io
import json
import os
import pickle

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
WDS = "/srv/scratch/bimrose2/drawing_agent_exp1/wds_dataset"
CACHE = os.path.join(WDS, "eval_cache_v15.pkl")
GT_DIR = os.path.join(WDS, "gt_meshes_v15")
N = 96


def decode_png(b: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(b))
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img.convert("RGB")


def main():
    with open(CACHE, "rb") as f:
        cache = pickle.load(f)
    keys = [k for k in cache["pools"]["certified"]
            if os.path.exists(os.path.join(GT_DIR, f"{k}.stl"))][:N]
    assert len(keys) == N, len(keys)

    draw_dir = os.path.join(EXP, "artifacts", "drawings")
    os.makedirs(draw_dir, exist_ok=True)
    manifest = []
    for k in keys:
        png = os.path.join(draw_dir, f"{k}.png")
        if not os.path.exists(png):
            decode_png(cache["samples"][k]["png"]).save(png)
        manifest.append({"uid": k, "png": png,
                         "gt_stl": os.path.join(GT_DIR, f"{k}.stl")})
    with open(os.path.join(EXP, "artifacts", "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"wrote {len(manifest)} entries -> artifacts/manifest.json")


if __name__ == "__main__":
    main()
