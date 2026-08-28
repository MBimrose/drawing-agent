"""Volumetric IoU between meshes — adapted verbatim from
vendor/drawing-vlm/train_v14/geom/iou.py (headline metric: centered IoU).

CLI:  python iou.py <pred.stl> <gt.stl>   -> prints one JSON record.
"""
from __future__ import annotations

import numpy as np
import trimesh

try:
    import manifold3d
except ImportError:  # pragma: no cover
    manifold3d = None


def center_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    m = mesh.copy()
    bb_min, bb_max = m.bounds
    m.apply_translation(-0.5 * (bb_min + bb_max))
    return m


def _to_manifold(mesh: trimesh.Trimesh):
    if manifold3d is None or mesh is None or len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        return None
    try:
        mesh = mesh.process(validate=False)
    except Exception:
        pass
    verts = np.asarray(mesh.vertices, dtype=np.float32)
    faces = np.asarray(mesh.faces, dtype=np.uint32)
    m = None
    for _attempt in range(4):
        try:
            m = manifold3d.Manifold(manifold3d.Mesh(vert_properties=verts, tri_verts=faces))
            break
        except Exception:
            m = None
            import time as _t
            _t.sleep(0.25 * (_attempt + 1))
    if m is None:
        return None
    try:
        if m.volume() == 0.0:
            return None
    except Exception:
        return None
    return m


def _trimesh_iou_fallback(mesh_a: trimesh.Trimesh, mesh_b: trimesh.Trimesh) -> float:
    try:
        inter = mesh_a.intersection(mesh_b)
        uni = mesh_a.union(mesh_b)
        if inter is None or uni is None:
            return 0.0
        v_inter = abs(inter.volume)
        v_uni = abs(uni.volume)
        if v_uni <= 0:
            return 0.0
        iou = v_inter / v_uni
        if iou > 1.0 + 1e-6:
            return 0.0
        return min(iou, 1.0)
    except Exception:
        return 0.0


def mesh_iou(mesh_a: trimesh.Trimesh, mesh_b: trimesh.Trimesh) -> float:
    if mesh_a is None or mesh_b is None:
        return 0.0
    ma, mb = _to_manifold(mesh_a), _to_manifold(mesh_b)
    if ma is None or mb is None:
        return _trimesh_iou_fallback(mesh_a, mesh_b)
    try:
        inter = manifold3d.Manifold.batch_boolean([ma, mb], manifold3d.OpType.Intersect)
    except Exception:
        return _trimesh_iou_fallback(mesh_a, mesh_b)
    if inter is None:
        return _trimesh_iou_fallback(mesh_a, mesh_b)
    try:
        v_inter = abs(inter.volume())
        va, vb = ma.volume(), mb.volume()
        if va < 0 or vb < 0:
            uni = manifold3d.Manifold.batch_boolean([ma, mb], manifold3d.OpType.Add)
            if uni is None:
                return _trimesh_iou_fallback(mesh_a, mesh_b)
            v_uni = abs(uni.volume())
        else:
            v_uni = abs(va) + abs(vb) - v_inter
    except Exception:
        return _trimesh_iou_fallback(mesh_a, mesh_b)
    if v_uni <= 0:
        return 0.0
    iou = v_inter / v_uni
    if iou > 1.0 + 1e-6:
        return _trimesh_iou_fallback(mesh_a, mesh_b)
    return min(iou, 1.0)


def load_mesh(path: str):
    try:
        m = trimesh.load(path, force="mesh")
        if m is None or len(m.faces) == 0:
            return None
        return m
    except Exception:
        return None


def iou_pair(pred_stl: str, gt_stl: str) -> dict:
    pred = load_mesh(pred_stl)
    gt = load_mesh(gt_stl)
    if pred is None or gt is None:
        return {"iou_raw": 0.0, "iou_centered": 0.0, "vol_pred": 0.0,
                "vol_gt": float(abs(gt.volume)) if gt is not None else 0.0,
                "mesh_ok": False}
    return {
        "mesh_ok": True,
        "vol_pred": float(abs(pred.volume)),
        "vol_gt": float(abs(gt.volume)),
        "iou_raw": mesh_iou(pred, gt),
        "iou_centered": mesh_iou(center_mesh(pred), center_mesh(gt)),
    }


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(iou_pair(sys.argv[1], sys.argv[2])))
