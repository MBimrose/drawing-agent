"""Worker: execute one candidate build123d script, keep STEP+STL, print feature JSON.

    python _exec_measure_one.py <code.py> <out.stl> <out.step>

Exec conventions mirror vendor exec_harness (temp cwd, script exports output.step).
Output (stdout, last line): JSON with exec/measure results. Never touches GT.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
import tempfile
import traceback


def measure(stl_path, step_path):
    rec = {}
    import trimesh
    m = trimesh.load(stl_path, force="mesh")
    ext = [float(v) for v in m.bounding_box.extents]
    rec["bbox_mm"] = [round(v, 3) for v in ext]
    rec["volume_mm3"] = round(float(abs(m.volume)), 2)
    rec["area_mm2"] = round(float(m.area), 2)
    rec["watertight"] = bool(m.is_watertight)
    rec["n_mesh_components"] = int(m.body_count)
    lo = min(ext) if min(ext) > 0 else 1e-9
    rec["aspect"] = round(max(ext) / lo, 2)
    bbox_vol = ext[0] * ext[1] * ext[2]
    rec["fill_frac"] = round(rec["volume_mm3"] / bbox_vol, 4) if bbox_vol > 0 else 0.0
    try:
        from build123d import GeomType, import_step
        shape = import_step(step_path)
        faces = shape.faces()
        rec["n_faces"] = len(faces)
        rec["n_planar_faces"] = len(faces.filter_by(GeomType.PLANE))
        rec["n_cylindrical_faces"] = len(faces.filter_by(GeomType.CYLINDER))
        rec["n_solids"] = len(shape.solids())
    except Exception as exc:  # noqa: BLE001
        rec["step_inspect_error"] = str(exc)[:200]
    return rec


def main() -> int:
    code_path, out_stl, out_step = sys.argv[1:4]
    with open(code_path, encoding="utf-8", errors="replace") as f:
        code = f.read()
    out_stl, out_step = os.path.abspath(out_stl), os.path.abspath(out_step)
    rec = {"exec_ok": False}
    keep = tempfile.TemporaryDirectory(prefix="b3dx_")
    with keep as td:
        os.chdir(td)
        g: dict = {"__name__": "__main__", "OUTPUT_PATH": "output.step"}
        try:
            exec(compile(code, "<generated>", "exec"), g)  # noqa: S102
        except SystemExit:
            pass
        except Exception:
            rec["error"] = traceback.format_exc()[-500:]
            print(json.dumps(rec))
            return 0
        step = os.path.join(td, "output.step")
        if not os.path.exists(step) or os.path.getsize(step) == 0:
            rec["error"] = "no output.step"
            print(json.dumps(rec))
            return 0
        shutil.copyfile(step, out_step)
        try:
            from build123d import Mesher, import_step
            shape = import_step(step)
            m = Mesher()
            m.add_shape(shape, angular_deflection=0.5)
            m.write(out_stl)
        except Exception:
            try:
                from build123d import export_stl, import_step
                shape = import_step(step)
                export_stl(shape, out_stl)
            except Exception:
                rec["error"] = "mesh failed: " + traceback.format_exc()[-300:]
                print(json.dumps(rec))
                return 0
        if not os.path.exists(out_stl) or os.path.getsize(out_stl) == 0:
            rec["error"] = "empty stl"
            print(json.dumps(rec))
            return 0
        rec["exec_ok"] = True
        try:
            rec.update(measure(out_stl, out_step))
        except Exception:
            rec["measure_error"] = traceback.format_exc()[-300:]
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
