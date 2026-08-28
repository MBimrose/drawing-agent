"""Render engineering drawings for exp2 parts with CONTROLLED dimensioning.

Uses the vendor step_to_drw legacy renderer (build_drawing_signal with
DRAW_RENDERER=legacy) but replaces its auto_dimension with a deterministic
edge dimensioner that supports two schemes:

  direct  : per-view bounding-box (overall) dimensions + every unique hard
            linear edge dimensioned (classic fully-direct dimensioning).
  chained : NO overall/bbox dimensions; every unique hard linear edge
            dimensioned EXCEPT edges whose real length matches a suppressed
            overall — the reader must sum chain segments (indirect
            dimensioning, the cadgenbench "hard" re-dimensioning).

Hole callouts are made deterministic (plain "⌀d THRU"), tolerances disabled.
A placed-dimension inventory is recorded per view for a solvability check.

Must run under /software/python-3.11.1/bin/python3.11 (build123d 0.10 +
draftwright deps + cairosvg) with vendor/step_to_drw on sys.path.
"""
from __future__ import annotations

import math
import os
import sys

VENDOR = "/srv/scratch/bimrose2/drawing-agent/vendor/step_to_drw"
if VENDOR not in sys.path:
    sys.path.insert(0, VENDOR)
os.environ["DRAW_RENDERER"] = "legacy"

from build123d import (  # noqa: E402
    Axis, Curve, ExtensionLine, GeomType, PageSize, Pos, Rectangle, ShapeList,
)

import dimensions as _dims_mod  # noqa: E402
from dimensions import filter_hard_edges, _draft_for_dimension, _format_dim  # noqa: E402

# Controlled-dimensioner state for the render in progress.
CTRL = {
    "scheme": "direct",       # "direct" | "chained"
    "suppress": [],           # real-mm lengths to hide in chained mode
    "inventory": [],          # [{view, label, mm, kind}]
    "cap": 12,                # max dims per view
}


def _orient(edge):
    try:
        s, t = edge.position_at(0), edge.position_at(1)
        dx, dy = abs(t.X - s.X), abs(t.Y - s.Y)
        if dx > 4 * dy:
            return "h"
        if dy > 4 * dx:
            return "v"
        return "o"
    except Exception:
        return "o"


def _is_suppressed(raw_mm):
    for s in CTRL["suppress"]:
        if abs(raw_mm - s) <= max(0.03 * s, 0.8):
            return True
    return False


def controlled_auto_dimension(visible_edges, view_name, draft_opts, tracker,
                              config, view_scale: float = 1.0):
    """Drop-in replacement for dimensions.auto_dimension (same signature)."""
    if len(visible_edges) < 2:
        return []
    edges = filter_hard_edges(visible_edges)
    if len(edges) < 2:
        return []
    inv_scale = 1.0 / view_scale if abs(view_scale) > 1e-9 else 1.0

    dims = []
    seen = set()                     # (rounded_mm, orientation)
    slot_idx = [0]
    offset_step = 6.0

    def next_offset(side=1):
        base = getattr(config, "dim_offset_min_mm", 8.0)
        slot = base + (slot_idx[0] % 5) * offset_step
        actual_side = side if slot_idx[0] < 5 else -side
        slot_idx[0] += 1
        return slot if actual_side > 0 else -slot

    def add_dim(edge, raw_mm, kind):
        label = _format_dim(raw_mm)
        smart_draft = _draft_for_dimension(raw_mm, draft_opts)
        offset = next_offset(1 if kind != "bbox_y" else -1)
        try:
            dim = ExtensionLine(border=edge, offset=abs(offset),
                                draft=smart_draft, label=label)
        except Exception:
            return False
        dims.append(dim)
        CTRL["inventory"].append(
            {"view": view_name, "label": label, "mm": round(raw_mm, 2), "kind": kind})
        return True

    # 1. Overall (bounding-box) dims — DIRECT scheme only.
    bbox = Curve(edges).bounding_box()
    if CTRL["scheme"] == "direct":
        perimeter = Pos(*bbox.center()) * Rectangle(bbox.size.X, bbox.size.Y)
        sx = perimeter.edges().sort_by(Axis.X)
        sy = perimeter.edges().sort_by(Axis.Y)
        for edge, kind, orient_key in [(sy[0], "bbox_x", "h"), (sx[-1], "bbox_y", "v")]:
            raw = edge.length * inv_scale
            if add_dim(edge, raw, kind):
                seen.add((round(raw * 2) / 2.0, orient_key))

    # 2. Feature dims: every unique (length, orientation) hard LINE edge.
    linear = [e for e in edges if e.geom_type == GeomType.LINE]
    linear.sort(key=lambda e: e.length, reverse=True)
    for e in linear:
        if len(dims) >= CTRL["cap"]:
            break
        raw = e.length * inv_scale
        if raw < 2.5:
            continue
        key = (round(raw * 2) / 2.0, _orient(e))
        if key in seen:
            continue
        if CTRL["scheme"] == "chained" and _is_suppressed(raw):
            seen.add(key)  # never place it, even via another same-length edge
            continue
        if add_dim(e, raw, "edge"):
            seen.add(key)
    return dims


def _plain_hole_callout(rng, diameter_mm, font_size, *, count=1, allow_typ=True):
    if diameter_mm < 1.0:
        return None
    label = (f"{count}X " if count > 1 else "") + f"⌀{_format_dim(diameter_mm)} THRU"
    CTRL["inventory"].append({"view": "?", "label": label,
                              "mm": round(diameter_mm, 2), "kind": "hole"})
    return label


def _plain_radius_callout(rng, radius_mm, *, count=1):
    if radius_mm <= 0:
        return ""
    label = (f"{count}X " if count > 1 else "") + f"R{_format_dim(radius_mm)}"
    CTRL["inventory"].append({"view": "?", "label": label,
                              "mm": round(radius_mm, 2), "kind": "radius"})
    return label


# Install the controlled dimensioner (draw_generator imports these lazily at
# call time, so patching module attributes is sufficient).
_dims_mod.auto_dimension = controlled_auto_dimension
_dims_mod._generate_hole_callout = _plain_hole_callout
_dims_mod._radius_callout = _plain_radius_callout


def render_drawing(part, uid, scheme, suppress, out_dir, seed=0,
                   png_width=2200):
    """Render one drawing; returns (png_path, inventory) or (None, None)."""
    from config import DrawingConfig
    from draw_generator import build_drawing_signal
    import cairosvg

    CTRL["scheme"] = scheme
    CTRL["suppress"] = list(suppress or [])
    CTRL["inventory"] = []

    cfg = DrawingConfig(seed=seed, tolerance_probability=0.0,
                        scale_jitter=0.03, layout_jitter=1.5,
                        font_size_min=4.5, font_size_max=4.5,
                        renderer="legacy")
    svg = build_drawing_signal(part, "grid_2x2", PageSize.A3, cfg, 1,
                               uid, out_dir, style_name="modern_iso",
                               dim_strategy="heavy", svg_only=True)
    if svg is None:
        return None, None
    png_path = os.path.join(out_dir, f"{uid}.png")
    cairosvg.svg2png(url=str(svg), write_to=png_path, output_width=png_width)
    try:
        os.unlink(str(svg))
    except OSError:
        pass
    return png_path, list(CTRL["inventory"])


def check_required(inventory, required_mm):
    """Return the required values (real mm) with no matching placed label."""
    placed = [rec["mm"] for rec in inventory]
    missing = []
    for want in required_mm:
        if not any(abs(p - want) <= max(0.02 * want, 0.6) for p in placed):
            missing.append(want)
    return missing
