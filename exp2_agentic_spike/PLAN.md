# Exp 2 — Agentic-harness spike (data-engine feasibility)

**Question:** on ~20 fresh drawings, does an agentic loop with geometry feedback beat the SAME
model single-shot — especially on indirectly-dimensioned drawings? A clear win (and usable
plan+code trajectories) is the case for an agentic data engine feeding rft_v3.

**Design:**
- **Data (local):** generate ~20 parts with `vendor/step_to_drw` (draw_generator.py etc.):
  ~10 with standard/direct dimensioning, ~10 hard (indirect/chained dimensioning if the
  generator supports it — see dimensions.py / generate_dimension_test_samples.py). Keep
  drawing PNG + GT build123d code + GT STEP/STL per part. Fresh seeds → no train-set overlap.
- **Solver model** (try in order):
  1. Kimi K3 via router/direct — verify image input actually works with one test call first.
  2. Qwen3-VL-235B relaunched on this box's idle H200s via
     `/srv/scratch/bimrose2/serve_qwen3_vl_235b.sh` (see docs/context.md caveats).
  3. Fallback two-model: GLM-OCR (serv-11:8000) extracts a dimension table/description;
     Kimi K3 (text) codes against it; loop feedback stays textual (validate/measure numbers).
- **Two arms, same model, same drawings:**
  - *Single-shot:* one completion from drawing (+ system prompt), execute, score.
  - *Agentic:* iterative loop (~10–15 turns budget) with execute + validity gate + measure/
    bbox feedback + render-compare (if solver has vision). Prefer dsh (headless or Python SDK
    with build123d-mcp attached); if dsh integration burns more than ~1h, fall back to a plain
    scripted loop — the measurement matters, not the framework. Note which was used.
  - Both arms use the cadgenbench prompt lessons (dimension-chain, named parameters, priority
    order) so the delta isolates the *loop*, not the prompt.
- **Scoring:** centered volumetric IoU vs GT STL, adapted from
  `vendor/drawing-vlm/train_v14/geom/{exec_harness,iou}.py`.

**Deliverables:** harness + generation code here; per-drawing table (single-shot IoU vs agentic
IoU, turns, wall-clock) in RESULTS.md; accepted trajectories (plan + final code) under
`trajectories/`; verdict: does agentic lift the hard tail enough to justify the data engine?

**Hygiene:** if you launch the VL server, verify port 8002 free first, log it, and kill it when
the experiment ends. Execute generated scripts in temp dirs outside the repo.

---

## Progress log (2026-08-27)

- **Data: DONE.** 20 fresh parts (10 std / 10 hard), 7 parametric families
  (steps3, notchplate, lbracket, tblock, shaft, uchannel, bossplate), fresh string
  seeds (`exp2-fresh-2026/...`), no train-set overlap (parts authored here, not drawn
  from Zero-To-CAD). Drawings rendered with the vendor legacy renderer
  (`DRAW_RENDERER=legacy`, A3, modern_iso, 2200px PNG) but with a **controlled
  dimensioner** (`gen/render_drawings.py`) replacing `dimensions.auto_dimension`:
  - std split = `direct` scheme: per-view overall (bbox) dims + every unique hard edge;
  - hard split = `chained` scheme: overalls suppressed by length-match, only chain
    segments dimmed (e.g. steps3 shows 28/21/17 but never 66) — the cadgenbench
    "indirect re-dimensioning" pattern.
  Hole callouts deterministic (`⌀d THRU`), tolerances off. Post-render solvability
  check verifies every required value is actually placed: **20/20 ok** (retry loop
  with fresh layout seeds). GT code/STEP/STL + dims inventory under `artifacts/`
  (gitignored), manifest at `artifacts/manifest.json`.
- **Solver: Kimi K3 via hub router** (wpk-serv-07:3456, anthropic-messages).
  Image input VERIFIED with a live call (read text out of a test PNG). No VL server
  launched on this box (GPUs untouched). Harness = plain scripted loop (dsh skipped —
  measurement over framework; noted for RESULTS).
- Arm design: turn-1 completion is scored as the single-shot arm AND seeds the agentic
  loop (same sample → the delta isolates the loop, no sampling noise between arms).
