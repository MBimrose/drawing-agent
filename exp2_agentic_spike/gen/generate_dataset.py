"""Generate the exp2 dataset: 20 fresh parts (10 std, 10 hard) with
GT code / STEP / STL and controlled-dimension drawings.

Run under /software/python-3.11.1/bin/python3.11:

    python3.11 gen/generate_dataset.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from part_families import ROSTER, make_part  # noqa: E402
from render_drawings import render_drawing, check_required  # noqa: E402

PY = sys.executable
EXEC_HARNESS = os.path.join(EXP, "harness", "exec_harness.py")
PARTS_DIR = os.path.join(EXP, "artifacts", "parts")
DRW_DIR = os.path.join(EXP, "artifacts", "drawings")


def build_gt(spec):
    uid = spec["uid"]
    pdir = os.path.join(PARTS_DIR, uid)
    os.makedirs(pdir, exist_ok=True)
    code_path = os.path.join(pdir, "gt_code.py")
    with open(code_path, "w") as f:
        f.write(spec["code"])
    stl = os.path.join(pdir, "gt.stl")
    step = os.path.join(pdir, "gt.step")
    r = subprocess.run([PY, EXEC_HARNESS, code_path, stl, step],
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"GT exec failed ({r.returncode}) for {uid}:\n{r.stderr[-2000:]}")
    return pdir, step, stl


def main():
    os.makedirs(DRW_DIR, exist_ok=True)
    from build123d import import_step

    manifest = []
    for split in ("std", "hard"):
        scheme = "direct" if split == "std" else "chained"
        for idx in range(len(ROSTER[split])):
            spec = make_part(split, idx)
            uid = spec["uid"]
            pdir, step, stl = build_gt(spec)
            part = import_step(step)
            bb = part.bounding_box()

            required = list(spec["required"]) + (
                spec["required_direct"] if scheme == "direct" else spec["required_chained"])
            suppress = spec["suppress"] if scheme == "chained" else []

            png = inv = None
            missing = required
            for attempt in range(5):
                png, inv = render_drawing(part, uid, scheme, suppress,
                                          DRW_DIR, seed=1000 * attempt + idx)
                if png is None:
                    continue
                missing = check_required(inv, required)
                if not missing:
                    break
            status = "ok" if (png and not missing) else f"MISSING {missing}"

            rec = {
                "uid": uid, "split": split, "family": spec["family"],
                "scheme": scheme, "params": spec["params"],
                "suppress": suppress, "required": required,
                "bbox_mm": [round(bb.size.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2)],
                "png": os.path.relpath(png, EXP) if png else None,
                "gt_stl": os.path.relpath(stl, EXP),
                "gt_step": os.path.relpath(step, EXP),
                "gt_code": os.path.relpath(os.path.join(pdir, "gt_code.py"), EXP),
                "status": status,
            }
            with open(os.path.join(pdir, "params.json"), "w") as f:
                json.dump(rec, f, indent=1)
            if inv is not None:
                with open(os.path.join(DRW_DIR, f"{uid}.dims.json"), "w") as f:
                    json.dump(inv, f, indent=1)
            manifest.append(rec)
            print(f"[{uid}] {status}  bbox={rec['bbox_mm']}  dims_placed={len(inv or [])}",
                  flush=True)

    with open(os.path.join(EXP, "artifacts", "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    n_ok = sum(1 for m in manifest if m["status"] == "ok")
    print(f"\n{n_ok}/{len(manifest)} parts fully solvable-dimensioned")


if __name__ == "__main__":
    main()
