"""Measure + render a candidate solid (subprocess; keeps OCCT out of the driver).

    python inspect_candidate.py <step> <stl> <out_png> <out_json>

Writes out_json with mesh/solid measurements (no verdicts — numbers only) and
out_png with Top / Front / Right orthographic line renders of the candidate,
using the same view conventions as the dataset drawings. PNG is best-effort:
failure to render still produces the JSON (render_ok records the outcome).
"""
from __future__ import annotations

import json
import math
import os
import sys


def measure(stl_path, step_path):
    rec = {}
    import trimesh
    m = trimesh.load(stl_path, force="mesh")
    ext = m.bounding_box.extents
    rec["bbox_mm"] = [round(float(v), 2) for v in ext]
    rec["volume_mm3"] = round(float(abs(m.volume)), 1)
    rec["watertight"] = bool(m.is_watertight)
    rec["n_mesh_components"] = int(m.body_count)
    try:
        from build123d import GeomType, import_step
        shape = import_step(step_path)
        faces = shape.faces()
        rec["n_faces"] = len(faces)
        rec["n_planar_faces"] = len(faces.filter_by(GeomType.PLANE))
        rec["n_cylindrical_faces"] = len(faces.filter_by(GeomType.CYLINDER))
        rec["n_solids"] = len(shape.solids())
        cyl_rads = sorted({round(f.radius, 2) for f in faces.filter_by(GeomType.CYLINDER)
                           if hasattr(f, "radius")})
        rec["cylindrical_radii_mm"] = cyl_rads[:12]
    except Exception as exc:  # noqa: BLE001
        rec["step_inspect_error"] = str(exc)[:200]
        shape = None
    return rec, shape


VIEWS = {  # name -> (origin, up)  — matches vendor VIEWPORT_PARAMS
    "top": ((0, 0, 100), (0, 1, 0)),
    "front": ((0, -100, 0), (0, 0, 1)),
    "right": ((100, 0, 0), (0, 0, 1)),
}


def render(shape, out_png, out_svg):
    from build123d import (Curve, ExportSVG, LineType, Pos, ShapeList, Text,
                           Unit)

    projections = {}
    for name, (origin, up) in VIEWS.items():
        vis, hid = shape.project_to_viewport(origin, up, look_at=(0, 0, 0))
        projections[name] = (ShapeList(vis), ShapeList(hid))

    def bbox_of(edges):
        bb = Curve(edges).bounding_box()
        return bb.min.X, bb.min.Y, bb.max.X, bb.max.Y

    GAP = 25.0
    boxes = {n: bbox_of(v + h if h else v) for n, (v, h) in projections.items()}
    fw = boxes["front"][2] - boxes["front"][0]
    fh = boxes["front"][3] - boxes["front"][1]
    th = boxes["top"][3] - boxes["top"][1]

    # front at origin; top above front; right to the right of front.
    offsets = {
        "front": (-boxes["front"][0], -boxes["front"][1]),
        "top": (-boxes["top"][0], fh + GAP - boxes["top"][1]),
        "right": (fw + GAP - boxes["right"][0], -boxes["right"][1]),
    }

    exporter = ExportSVG(unit=Unit.MM, margin=8)
    exporter.add_layer("Visible", line_weight=0.4)
    exporter.add_layer("Hidden", line_color=(120, 120, 120),
                       line_type=LineType.ISO_DOT)
    exporter.add_layer("Text", line_weight=0.25)
    labels = []
    for name, (vis, hid) in projections.items():
        dx, dy = offsets[name]
        mv = ShapeList([Pos(dx, dy, 0) * e for e in vis])
        exporter.add_shape(mv, layer="Visible")
        if hid:
            mh = ShapeList([Pos(dx, dy, 0) * e for e in hid])
            exporter.add_shape(mh, layer="Hidden")
        bb = boxes[name]
        cx = dx + (bb[0] + bb[2]) / 2
        top_y = dy + bb[3]
        labels.append(Pos(cx, top_y + 8, 0) * Text(name.upper(), 6))
    # place labels after views so text never vanishes under geometry
    for t in labels:
        exporter.add_shape(t, layer="Text")
    exporter.write(out_svg)

    import cairosvg
    cairosvg.svg2png(url=out_svg, write_to=out_png, output_width=1400,
                     background_color="white")


def main():
    step, stl, out_png, out_json = sys.argv[1:5]
    rec, shape = measure(stl, step)
    rec["render_ok"] = False
    if shape is not None:
        try:
            out_svg = out_png + ".svg"
            render(shape, out_png, out_svg)
            os.unlink(out_svg)
            rec["render_ok"] = os.path.exists(out_png) and os.path.getsize(out_png) > 0
        except Exception as exc:  # noqa: BLE001
            rec["render_error"] = str(exc)[:200]
    with open(out_json, "w") as f:
        json.dump(rec, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
