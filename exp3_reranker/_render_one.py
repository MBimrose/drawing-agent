"""Render Top/Front/Right orthographic line views of one candidate STEP -> PNG.

Adapted from exp2_agentic_spike/harness/inspect_candidate.py (same view
conventions as the dataset drawings). Run under /software/python-3.11.1
(build123d + cairosvg).

    python _render_one.py <step> <out_png>
"""
from __future__ import annotations

import os
import sys

VIEWS = {  # name -> (origin, up) — matches vendor VIEWPORT_PARAMS
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
    for t in labels:
        exporter.add_shape(t, layer="Text")
    exporter.write(out_svg)

    import cairosvg
    cairosvg.svg2png(url=out_svg, write_to=out_png, output_width=1100,
                     background_color="white")


def main():
    step, out_png = sys.argv[1:3]
    from build123d import import_step
    shape = import_step(step)
    out_svg = out_png + ".svg"
    render(shape, out_png, out_svg)
    os.unlink(out_svg)
    assert os.path.exists(out_png) and os.path.getsize(out_png) > 0
    print("ok")


if __name__ == "__main__":
    main()
