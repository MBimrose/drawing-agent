# Exp 3 results — Best-of-N selection policies vs the +0.047 oracle gap

**Date:** 2026-08-28 · **Data:** exp1's persisted 96 samples × 4 draws (e24-rft
ckpt-3250 best-of-4 rerun), all selection done offline; no new champion inference.
**Deployed baseline** 0.8756 (first-executing draw + repair), **oracle ceiling** 0.9222
(+0.0466). A policy counts as a WIN only if its paired 20k-bootstrap 95% CI vs deployed
excludes zero.

## TL;DR

TBD (after VLM rows)

## Method

- Selection-time inputs only: candidate code, re-executed candidate geometry, and the
  drawing PNG. GT meshes / shard IoUs are used exclusively to score a policy's pick.
- All 384 candidates re-executed CPU-parallel (36 s at 64 workers): **384/384 exec_ok
  agreement** with the exp1 shards; volumes match exp1's persisted STLs to ≤1e-6
  relative — execution is deterministic, so offline evaluation is faithful.
- Policies pick among shard-executing draws; when none execute (1 sample) every policy
  inherits the deployed repair fallback — policies differ only where a choice exists.
- Paired evaluation: per-sample IoU(policy pick) − IoU(deployed pick), 20k-resample
  paired bootstrap (same machinery as exp1's `analyze_bo4.py`).
- "gross18 fixed" = of exp1's 18 samples with oracle−deployed gap >0.10 (79% of gap
  mass), how many where the policy recovers ≥50% of that sample's gap.

### Signals

1. **Cross-candidate consensus** (no drawing needed): per executing draw, median
   scale-free geometric distance to the other executing draws — max |log ratio| over
   sorted bbox extents and volume^(1/3) (`policies.geo_dist`). Mis-scaled/mis-shaped
   draws sit far from the cluster the other samples form.
2. **Drawing-view aspect consistency**: the drawings ink-code geometry in black/gray
   and annotations in blue, so a blue-filter + connected components + orthographic
   alignment rules (front/right share the y-span, front/top share the x-span) yields
   per-view ink bounding boxes without any OCR (`drawing_views.py`). Extraction is
   self-validating (top.w≈front.w, right.h≈front.h within 3% on ~95% of extractions);
   full front+top+right on 73/96 drawings, ≥2 usable views on 75/96 (15/18 of the
   gross-error set). Candidate mismatch = max |log(candidate bbox ratio / drawing view
   ratio)| over available views (scale-invariant — no need to read dimension text).
3. **Degenerate-solid checks** (tiny volume, sliver fill, extreme aspect,
   non-watertight, many solids) — measured, and a clear **negative result**, see below.
4. **VLM critic**: Kimi K3 via the hub router, one call per sample: drawing + up to 4
   candidate 3-view line renders (exp2's render conventions), candidates letter-labeled
   in key-seeded shuffled order (position-bias control), thinking-aware token budget,
   JSON verdict {scores 0–10, best, gross[]}. 94/96 samples eligible (≥2 rendered
   candidates); the other 2 have ≤1 executing draw — nothing to choose.

## Policy table (ranked by mean IoU)

TBD — full table from policy_results.json after the VLM run.

## The headline no-model policy

**`combined c1a1 m0.05`** — score each executing draw
`consensus_med_dist + aspect_mismatch`, then switch away from the first-executing
draw only when the best-scoring draw beats it by >0.05:

- **0.8978 mean IoU, +0.0222 vs deployed, 95% CI [+0.0092, +0.0381] — significant.**
- Captures **47.7%** of the oracle gap; fixes 8/18 gross-error samples.
- Switches on only 13/96 samples and every switch gained IoU (+0.014 … +0.465);
  **zero** samples worsened. Cost: zero model calls; ~90 s of CPU pool time for
  re-exec + measurement of 4 candidates × 96 samples (renders not needed).

Per-switch audit:

| key | deployed | → pick | ΔIoU | gross-error sample |
|---|---|---|---|---|
| 08734382 | d0 0.166 | d1 0.631 | +0.465 | yes |
| 00199e66 | d0 0.683 | d1 1.000 | +0.317 | yes |
| 058f2c3a | d0 0.739 | d1 0.998 | +0.258 | yes |
| 0fdd267e | d1 0.791 | d3 1.000 | +0.209 | yes |
| 05d7977c | d1 0.793 | d2 1.000 | +0.207 | yes |
| 04a4e152 | d0 0.662 | d2 0.842 | +0.180 | yes |
| 0f65741c | d0 0.810 | d1 0.959 | +0.149 | yes |
| 0b611efc | d0 0.631 | d1 0.780 | +0.149 | yes |
| 0e14533a | d0 0.912 | d1 0.980 | +0.068 | no |
| 02c2c534 | d1 0.000 | d3 0.048 | +0.048 | no |
| 0ce4f582 | d0 0.816 | d1 0.857 | +0.041 | yes |
| 0120e88c | d0 0.959 | d1 0.988 | +0.030 | no |
| 09a06a3c | d0 0.698 | d1 0.712 | +0.014 | no |

## Ablations (heuristics)

| variant | Δ vs deployed | 95% CI | sig | notes |
|---|---|---|---|---|
| combined c1a1 margin 0.05 | +0.0222 | [+0.0092, +0.0381] | ✓ | headline |
| combined c1a2 (aspect ×2) | +0.0227 | [+0.0095, +0.0387] | ✓ | +1 break (−0.052) |
| combined, margin 0 | +0.0211 | [+0.0051, +0.0386] | ✓ | 6 breaks, worst −0.201 |
| combined, margin 0.10 | +0.0144 | [+0.0044, +0.0263] | ✓ | too timid |
| aspect only (c0a1 m0.05) | +0.0162 | [+0.0051, +0.0303] | ✓ | |
| consensus only (c1a0 m0.05) | +0.0090 | [+0.0017, +0.0191] | ✓ | |
| aspect-best always | +0.0172 | [+0.0058, +0.0315] | ✓ | 2 breaks |
| consensus-medoid always | +0.0128 | [+0.0001, +0.0264] | ✓ (barely) | 5 breaks, worst −0.201 |
| gate degen+consensus+aspect (flag→next-best) | +0.0096 | [+0.0015, +0.0202] | ✓ | gating < scoring |
| degenerate gate only | −0.0091 | [−0.0219, 0.0000] | ✗ | HARMFUL |
| random-exec (expectation) | −0.0059 | [−0.0206, +0.0085] | ✗ | first-exec beats random |
| greedy (draw 0 only) | −0.0885 | [−0.1444, −0.0389] | ✗ | |

Takeaways:

- **Consensus and aspect stack** (+0.009 and +0.016 alone → +0.022 together), and the
  switch-margin is what removes the breaks (margin 0 → 6 breaks, worst −0.20).
- **Degenerate-solid checks are a dead end on this champion**: execution already
  filters junk. The bad candidates are watertight single solids that are *mis-scaled or
  mis-shaped*; `not_watertight`/`many_solids` fire mostly on good candidates (median
  IoU 0.86 / 0.98), so gating on them loses −0.009. None of `tiny_volume`,
  `sliver_fill`, `extreme_aspect` fire at all on the 347 executing candidates.
- Hard *gating* (first-exec unless flagged, then next-best) underperforms soft
  *scoring* with a switch margin at equal information (+0.010 vs +0.022).

## VLM critic (Kimi K3)

TBD

## `claude-qwen36-27b-build123d-critic` probe

Listed by the router's /v1/models, but calls return backend `NotFoundError` ("The model
`qwen36-27b-build123d-critic` does not exist") — its qwen3.6 backend (wpk-serv-06:8000)
is stopped. Two probe calls, both fail; router itself healthy (Kimi answers in <1 s).
**Not usable as-is → excluded**, per plan.

## Recommended deployable policy

TBD

## Limitations

TBD
