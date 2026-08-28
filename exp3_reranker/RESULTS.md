# Exp 3 results — Best-of-N selection policies vs the +0.047 oracle gap

**Date:** 2026-08-28 · **Data:** exp1's persisted 96 samples × 4 draws (e24-rft
ckpt-3250 best-of-4 rerun), all selection done offline; no new champion inference.
**Deployed baseline** 0.8756 (first-executing draw + repair), **oracle ceiling** 0.9222
(+0.0466). A policy counts as a WIN only if its paired 20k-bootstrap 95% CI vs deployed
excludes zero.

## TL;DR

**A zero-model-call heuristic captures ~48% of the oracle gap with zero regressions:**
score each executing draw by cross-candidate geometric consensus + drawing-view aspect
mismatch, and leave the deployed first-exec pick unless a sibling beats it by a clear
margin. **0.8978 mean IoU, +0.0222 vs deployed, 95% CI [+0.0092, +0.0381]** — 13
switches, all 13 gained IoU, 8/18 gross-error samples fixed. The Kimi K3 VLM critic is
NOT a win as a full reranker (+0.0133, CI crosses zero: it fixes the most gross errors,
11/18, but mis-reranks near-ties often enough to wash that out), and as a veto on the
heuristic it only subtracts. **Recommendation: deploy the heuristic; skip the VLM
critic at this champion's error profile.**

## Policy table (curated; full table in `policy_results.json`)

| policy | mean IoU | Δ vs deployed | 95% CI | sig | % gap | gross18 fixed | broken >0.01 (worst) | model calls |
|---|---|---|---|---|---|---|---|---|
| oracle (ceiling) | 0.9222 | +0.0466 | [+0.031, +0.064] | ✓ | 100% | 18/18 | 0 | 0 |
| **combined consensus+aspect, margin 0.05** | **0.8978** | **+0.0222** | **[+0.0092, +0.0381]** | **✓** | **48%** | **8/18** | **0** | **0** |
| combined, aspect ×2 | 0.8982 | +0.0227 | [+0.0095, +0.0387] | ✓ | 49% | 8/18 | 1 (−0.052) | 0 |
| shape-consensus + aspect ×2, margin 0.1 | 0.8981 | +0.0226 | [+0.0093, +0.0384] | ✓ | 48% | 9/18 | 1 (−0.052) | 0 |
| hybrid2: heuristic switch + VLM must agree | 0.8930 | +0.0174 | [+0.0070, +0.0297] | ✓ | 37% | 7/18 | 0 | 13 |
| aspect-best (always) | 0.8928 | +0.0172 | [+0.0058, +0.0315] | ✓ | 37% | 6/18 | 2 (−0.052) | 0 |
| hybrid: heuristic flags → VLM adjudicates | 0.8920 | +0.0165 | [+0.0060, +0.0288] | ✓ | 35% | 7/18 | 1 (−0.040) | 13 |
| shape-consensus + aspect, margin 0.05 | 0.8930 | +0.0175 | [+0.0067, +0.0302] | ✓ | 38% | 8/18 | 2 (−0.058) | 0 |
| VLM pick (Kimi K3, best-of-verdict) | 0.8888 | +0.0133 | [−0.0047, +0.0310] | ✗ | 29% | 11/18 | 12 (−0.416) | 91 |
| VLM score-argmax (ties→first-exec) | 0.8888 | +0.0133 | [−0.0047, +0.0310] | ✗ | 29% | 11/18 | 12 (−0.416) | 91 |
| VLM gate (first-exec unless flagged) | 0.8884 | +0.0129 | [−0.0043, +0.0297] | ✗ | 28% | 10/18 | 10 (−0.416) | 91 |
| consensus-medoid (always) | 0.8884 | +0.0128 | [+0.0001, +0.0264] | ✓ | 28% | 6/18 | 5 (−0.201) | 0 |
| gate: flag→next-best (degen+cons+aspect) | 0.8852 | +0.0096 | [+0.0015, +0.0202] | ✓ | 21% | 4/18 | 0 | 0 |
| consensus-only score, margin 0.05 | 0.8846 | +0.0090 | [+0.0017, +0.0191] | ✓ | 19% | 4/18 | 0 | 0 |
| deployed (first-exec + repair) | 0.8756 | 0 | — | — | 0 | 0/18 | 0 | 0 |
| random-exec (expectation) | 0.8697 | −0.0059 | [−0.0206, +0.0085] | ✗ | −13% | — | 31 | 0 |
| degenerate-gate only | 0.8665 | −0.0091 | [−0.0219, 0.0000] | ✗ | −20% | 0/18 | 3 (−0.416) | 0 |
| greedy (draw 0 only, no repair) | 0.7871 | −0.0885 | [−0.1444, −0.0389] | ✓(worse) | −190% | — | 10 | 0 |

## Method

- Selection-time inputs only: candidate code, re-executed candidate geometry, and the
  drawing PNG. GT meshes / shard IoUs are used exclusively to score a policy's pick.
- All 384 candidates re-executed CPU-parallel (36 s at 64 workers): **384/384 exec_ok
  agreement** with the exp1 shards; volumes match exp1's persisted STLs to ≤1e-6
  relative — execution is deterministic, so offline evaluation is faithful.
- Policies pick among shard-executing draws; when none execute (1 sample) every policy
  inherits the deployed repair fallback.
- Paired evaluation: per-sample IoU(policy pick) − IoU(deployed pick), 20k-resample
  paired bootstrap (exp1's `analyze_bo4.py` machinery, seed-matched).
- "gross18 fixed" = of exp1's 18 samples with oracle−deployed gap >0.10 (79% of the
  gap mass), how many where the policy recovers ≥50% of that sample's gap.

### Selection signals

1. **Cross-candidate bbox/volume consensus** (no drawing needed): per executing draw,
   median scale-free distance to sibling draws — max |log ratio| over sorted bbox
   extents and volume^(1/3).
2. **Drawing-view aspect consistency**: the drawings ink-code geometry in black/gray
   and annotations in blue; a blue-filter + connected components + orthographic
   alignment (front/right share the y-span, front/top share the x-span) yields
   per-view ink bboxes with no OCR (`drawing_views.py`). Self-validating (cross-view
   scale checks within 3% on ~95% of extractions); ≥2 usable views on 75/96 drawings
   (15/18 of the gross-error set). Candidate mismatch = max |log(candidate bbox ratio /
   drawing view ratio)| — scale-invariant, no dimension-text parsing.
3. **Shape-space consensus**: pairwise candidate-vs-candidate centered mesh IoU
   (`pairwise_iou.py`, 549 pairs in 25 s, vendor metric, GT-free) — sees
   internal-feature differences bbox consensus is blind to.
4. **Degenerate-solid checks** — measured, and a clear negative result (below).
5. **VLM critic**: Kimi K3 via hub router; one call per sample: drawing + up to 4
   candidate 3-view line renders (exp2 conventions), letter-labeled, key-seeded
   shuffled order (position-bias control); JSON verdict {scores 0–10, best, gross[]}.
   93/96 verdicts (1 parse failure, 2 samples with <2 rendered candidates).

## The recommended policy, audited

`score(draw) = consensus_med_dist + aspect_mismatch`; switch from first-exec to the
best-scoring draw only when its score is better by >0.05. Every switch it made
(13/96) gained IoU:

| key | deployed | → pick | ΔIoU | gross | | key | deployed | → pick | ΔIoU | gross |
|---|---|---|---|---|---|---|---|---|---|---|
| 08734382 | d0 0.166 | d1 0.631 | +0.465 | ✓ | | 0b611efc | d0 0.631 | d1 0.780 | +0.149 | ✓ |
| 00199e66 | d0 0.683 | d1 1.000 | +0.317 | ✓ | | 0e14533a | d0 0.912 | d1 0.980 | +0.068 | |
| 058f2c3a | d0 0.739 | d1 0.998 | +0.258 | ✓ | | 02c2c534 | d1 0.000 | d3 0.048 | +0.048 | |
| 0fdd267e | d1 0.791 | d3 1.000 | +0.209 | ✓ | | 0ce4f582 | d0 0.816 | d1 0.857 | +0.041 | ✓ |
| 05d7977c | d1 0.793 | d2 1.000 | +0.207 | ✓ | | 0120e88c | d0 0.959 | d1 0.988 | +0.030 | |
| 04a4e152 | d0 0.662 | d2 0.842 | +0.180 | ✓ | | 09a06a3c | d0 0.698 | d1 0.712 | +0.014 | |
| 0f65741c | d0 0.810 | d1 0.959 | +0.149 | ✓ | | | | | | |

Deployment shape: generate all 4 draws up front (no early stop — ~3.5× the generation
compute of the early-stopping policy; exp1 measured the full 4-draw pass at ~19 min for
96 samples on 16 GPUs), execute + tessellate + measure all draws (<1 s CPU per
candidate amortized), extract drawing-view ratios once per drawing (~0.4 s), pick.
No model calls, no renders needed.

## Ablations (heuristics)

| variant | Δ | CI | note |
|---|---|---|---|
| combined, margin 0.05 | +0.0222 | [+0.0092, +0.0381] | headline |
| combined, margin 0 | +0.0211 | [+0.0051, +0.0386] | 6 breaks, worst −0.201 |
| combined, margin 0.10 | +0.0144 | [+0.0044, +0.0263] | too timid |
| aspect term only | +0.0162 | [+0.0051, +0.0303] | |
| consensus term only | +0.0090 | [+0.0017, +0.0191] | |
| shape-consensus instead of bbox | +0.0175 | [+0.0067, +0.0302] | 2 breaks |
| + shape as third term (best of grid) | +0.0175 | [+0.0067, +0.0302] | no stacking gain |
| hard gate instead of scored margin | +0.0096 | [+0.0015, +0.0202] | gating < scoring |

- **Consensus and aspect stack** (+0.009, +0.016 alone → +0.022 together); the switch
  margin is what removes regressions (margin 0 → 6 breaks, worst −0.201).
- **Degenerate-solid checks are a dead end on this champion**: execution already
  filters junk. Bad candidates are watertight single solids that are *mis-scaled or
  mis-shaped*; `not_watertight`/`many_solids` fire mostly on good candidates (median
  IoU 0.86/0.98), so gating on them loses −0.009; `tiny_volume`/`sliver_fill`/
  `extreme_aspect` never fire on the 347 executing candidates.
- **Shape consensus beats bbox consensus alone** (+0.014 vs +0.009) but does not add
  on top of bbox+aspect. Structural reason: in ALL 10 gross-error samples the headline
  policy misses, the draws share identical bboxes and the *majority* of draws share the
  deployed draw's wrong shape — consensus of any kind cannot elect a minority-correct
  draw, and aspect can't see internal features. That residual (~half the gap) needs
  drawing-aware feature judgment.

## VLM critic (Kimi K3): not a win

- Cost: 91 calls, 0.76M in / 1.25M out tokens, median 135 s p90 521 s per call;
  ~110 min wall at 4-way concurrency (the hub backend degrades badly above ~3–4
  concurrent vision calls: at 10 workers, 900 s timeouts + retry churn).
- Verdict quality: picks an oracle-best draw on 55/93 samples; per-candidate scores
  correlate with IoU only loosely (score ≤3 → mean IoU 0.72; score ≥8 → 0.93);
  "gross" flags split 21 right / 21 wrong.
- **vlm-pick +0.0133 [−0.0047, +0.0310] — not significant.** It fixes the most
  gross-error samples of any policy (11/18) but re-ranks near-ties it should leave
  alone: 12 samples broken, worst −0.416 (10dff308: moved off a 1.000 d0 to a 0.584
  sibling). The failure mode anticipated in exp1 ("a learned critic that ranks
  near-ties adds little") is exactly what materializes — and it costs.
- Hybrids ARE significant but bounded by their heuristic component: heuristic-flags→VLM
  +0.0165, heuristic+VLM-agreement +0.0174 — both below the pure heuristic +0.0222,
  because the VLM's only marginal action was to veto correct switches. Its single
  hybrid2 veto was 08734382 — the largest gain in the set (+0.465): the drawing shows
  an open U-channel, the volumetrically-best draw models it as a closed box, and the
  VLM (defensibly, feature-wise) calls that gross — but centered volumetric IoU
  disagrees. Feature-correctness and volumetric IoU are not the same objective, and
  the critic optimizes the wrong one on exactly the samples that matter.

## `claude-qwen36-27b-build123d-critic` probe

Router lists it; calls return backend `NotFoundError` ("The model
`qwen36-27b-build123d-critic` does not exist") — its qwen3.6 backend
(wpk-serv-06:8000) is stopped. Two probe calls, both fail; router healthy (Kimi
answers in <1 s). **Not usable as-is → excluded**, per plan.

## Limitations

- **n=96, one checkpoint (e24-rft ckpt-3250), one draw budget (4).** The margin and
  weights of the headline policy were chosen on this same set; the honest claim is the
  sensitivity band, not the point value: every margin∈{0, 0.05, 0.10} × weight variant
  tested is CI-significant (+0.009 … +0.023), so the sign is robust even if the exact
  +0.022 is optimistic. Validation on a fresh pool (or the next checkpoint) is cheap:
  the whole heuristic pipeline is ~2 min of CPU.
- Aspect extraction relies on this dataset's drawing style (blue annotations, view
  alignment); 21/96 drawings yield <2 usable views and silently degrade the policy to
  consensus-only there.
- The VLM verdict is one prompt design, one model, temperature 0, one call per sample.
  A tuned variant (e.g., asked only "is the first pick grossly wrong vs the drawing?",
  or majority-of-3 sampling) might behave differently; what this experiment rules out
  is the cheap off-the-shelf version, not VLM critics as a class.
- Draw IoUs come from the exp1 rerun; its own noise floor vs the original run was
  ±0.001 (exp1 parity check), far below the effects reported.
- The 1 no-exec sample and 2 single-candidate samples are untouchable by any selection
  policy (~was already inside the deployed number).

## Artifacts

- `policy_results.json` (committed) — every policy row incl. the full threshold grids.
- `features.json`, `drawing_views.json`, `pairwise_iou.json` (committed) — selection
  features; `artifacts/vlm_kimi.json` + `.jsonl` (gitignored, on serv-06) — raw VLM
  replies + verdicts; candidate STL/STEP/renders under
  `/srv/scratch/bimrose2/drawing_agent_exp3/`.
- Code: `bo4data.py` (loader + paired-bootstrap eval), `rexec_features.py` +
  `_exec_measure_one.py`, `drawing_views.py`, `pairwise_iou.py`, `policies.py`,
  `render_candidates.py` + `_render_one.py`, `vlm_critic.py`, `vlm_diag.py`,
  `evaluate.py`.
