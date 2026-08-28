# Exp 2 — Agentic-harness spike: results

*(numbers being filled in — runs in flight)*

## Setup

- **Data**: 20 freshly generated parts (this repo, `gen/`), 7 parametric families,
  fresh seeds, zero overlap with any training corpus. Two splits:
  - **std** (n=10): fully **direct** dimensioning — per-view overall dims + every
    unique feature edge dimensioned.
  - **hard** (n=10): **indirect / chained** dimensioning — overall extents
    suppressed (length-matched) so only chain segments appear; the reader must sum
    segments (e.g. 28 + 21 + 17 = 66) to recover overalls. This reproduces the
    cadgenbench finding that indirect re-dimensioning is the failure mode
    (GPT-5.5 dropped 0.93 → 0.63 there).
  - Drawings: vendor step_to_drw legacy renderer, A3 modern_iso, 4 views
    (Top/Front/Right/ISO), deterministic hole callouts, no tolerances, 2200 px PNG.
    A post-render check verified every required value is actually placed on the
    sheet (20/20).
- **Solver**: Kimi K3 via the lab hub router (anthropic-messages,
  wpk-serv-07:3456); image input verified live before the run (option (a) of the
  plan — options (b)/(c) not needed). Secondary run: qwen3.8-27b (the
  drawing-vlm base model) via the same router, same drawings, same prompts, both
  arms, to measure loop lift on a weaker solver. No VL server was launched on
  wpk-serv-06 (GPUs untouched).
- **Harness**: plain scripted loop (`harness/run_arms.py`), not dsh — the dsh
  integration was skipped in favor of measurement time; noted per plan.
- **Arms** (same model, same drawing, same cadgenbench-informed system prompt —
  dimension-chain reading, named-parameter block, priority order):
  - *Single-shot*: the turn-1 completion, executed and scored.
  - *Agentic*: the SAME turn-1 completion seeds a loop (budget 12 model calls)
    whose feedback is measurements only — exec result / stderr, bbox, volume,
    face census, cylinder radii, plus a 3-view orthographic re-render of the
    model's own candidate. No GT values, no PASS/FAIL verdicts (PASS-tool trap).
    Model ends by replying FINAL; final answer = last executing candidate
    (checkpoint-first).
  - Sharing turn 1 between arms removes sampling noise from the delta: the
    difference IS the loop contribution.
- **Metric**: centered volumetric IoU vs GT STL (`harness/iou.py`, adapted
  verbatim from drawing-vlm `train_v14/geom/iou.py`, manifold3d + trimesh
  fallback). T=0.6, max_tokens 8000 both arms.

## Per-drawing results — Kimi K3 (primary)

*(table pending)*

## Split means

*(pending)*

## Secondary run — qwen3.8-27b (drawing-vlm base)

*(pending)*

## Verdict

*(pending)*
