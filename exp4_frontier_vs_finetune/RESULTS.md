# Exp 4 results — Frontier model + agentic harness vs the cluster fine-tune

**Date:** 2026-08-28 · **Eval:** the champion's own frozen 96-sample certified pool
(eval_cache_v15, key set verified identical to exp1's) · centered volumetric IoU vs
`gt_meshes_v15` · **Solver:** Kimi K3 via hub router, exp2 agentic harness.

## TL;DR — the fine-tune wins its home benchmark decisively

| Policy | Mean centered IoU | IoU≥0.8 (STaR gate) | exec |
|---|---|---|---|
| Kimi K3 single-shot | 0.549 | 35/96 | 73/96 |
| **Kimi K3 + agentic loop (12-call budget)** | **0.724** | **45/96** | **96/96** |
| Kimi agentic best-candidate (loop oracle) | 0.724 | 45/96 | — |
| e24-rft greedy (draw 0 only) | 0.787 | 71/96 | — |
| e24-rft deployed best-of-4 + repair | 0.876 | 77/96 | 95/96 |
| e24-rft oracle-of-4 | 0.922 | 85/96 | — |

**Kimi + loop lands 0.06 BELOW the champion's greedy single draw** (paired −0.063,
bootstrap 95% CI [−0.139, +0.015] — statistically indistinguishable from greedy) **and
0.15 below the deployed policy** (−0.152, CI [−0.208, −0.097] — decisive). The agentic
loop is worth +0.175 over Kimi single-shot (CI [+0.113, +0.241]; 30 wins, 0 regressions),
but nearly all of it is execution repair; it does not close the reading gap to a model
fine-tuned on this drawing distribution. **On this task, at this scale, fine-tuning beats
frontier+harness on-distribution — but the two fail on different parts** (see
complementarity below), which is exactly the configuration that makes Kimi+loop a useful
RFT teacher rather than a replacement.

## Setup

- **Data:** the SAME 96 samples exp1 rescored (first 96 keys of `pools["certified"]`
  with GT meshes — verified equal to exp1's key set). Drawings decoded from the eval
  cache exactly as the champion's eval does (RGBA over white, 1920×1280).
- **Arms** (exp2 harness, `harness/run_arms.py`): turn-1 completion = single-shot arm
  AND seed of the agentic loop (delta isolates the loop). Loop: budget 12 model calls,
  measurement-only feedback — exec/stderr, bbox/volume/face census/cylinder radii, one
  orthographic self-render per turn; no GT, no PASS verdicts; final = last executing
  candidate. T=0.6, max_tokens 16000 (exp2's 8k truncated Kimi's thinking).
- **Prompt:** exp2's cadgenbench-informed system prompt with the view-conventions
  paragraph adapted to the v15 sheet style (unlabeled third-angle views, SECTION views,
  ISO VIEW (NTS), ⌀/↓/⌵ callout symbols, C-chamfer notes).
- **Scoring:** `harness/iou.py` (verbatim exp2 copy = verbatim adaptation of
  train_v14/geom/iou.py); exec under /software/python-3.11.1 (build123d 0.10) in temp
  dirs outside the repo — same semantics as the champion's eval harness.
- **Harness fix along the way:** exp2's `is_final` matched the word FINAL anywhere in a
  reply. Kimi produced ~100k-char runaway-thinking turns (truncated, no code) that
  mentioned FINAL mid-deliberation; 7 parts were falsely terminated at turn 1. Fixed
  (FINAL must sit in the last 300 chars of a <2000-char reply; genuine FINALs observed
  ≤1.3k chars) and those parts rerun with the fixed code. exp2's published numbers are
  unaffected (all its FINAL replies were genuine). Transient router 502s (the router is
  shared with exp3) caused 15+1 mid-run failures, all retried to completion; final
  results have 96/96 scored, 0 errors.

## Where the loop's +0.175 comes from (and where it stops)

- **Execution repair is 92% of the lift** (+0.160 of +0.175). 23/96 turn-1 attempts
  produced no usable solid — runaway thinking that never reached code, build123d API
  slips, plus one script that executed but produced degenerate geometry. The loop
  repaired ALL of them (exec 73/96 → 96/96, mean recovered IoU 0.669).
- **Genuine refinement is real but small:** 8 executed parts improved from feedback
  (+0.015 overall), e.g. 0feed9be 0.000→0.897 (degenerate solid caught from
  measurements), 07bfb06a 0.870→0.942, 0eec11b2 0.752→0.889.
- **Zero regressions**; the model's FINAL matched its best candidate almost everywhere
  (best − final: mean +0.0003, max +0.020). 95/96 stopped on explicit FINAL, 1 hit the
  12-call budget.
- **The blind spot is unchanged from exp2:** confident misreads survive the loop.
  Kimi's worst misses are dimension/feature misreads (000bc5ac: read a 2 mm-wall
  hollow cap as a 2 mm-deep pocket, 0.453) and — new on this dataset — **view-convention
  misidentification**: the v15 sheets have unlabeled views, and on 10a652e2 Kimi took
  the top view for the front view and built the part in the wrong orientation (0.038 vs
  champion 1.000). Measurements of your own solid cannot contradict a wrong belief
  about the target.

## Difficulty structure — the two models fail on different parts

Buckets by champion deployed IoU (the eval metadata carries no difficulty labels):

| bucket | n | kimi ss | kimi agentic | champ deployed | champ oracle |
|---|---|---|---|---|---|
| champ-solved (dep≥0.95) | 53 | 0.615 | 0.780 | 0.986 | 0.992 |
| champ-partial (0.8≤dep<0.95) | 24 | 0.454 | 0.690 | 0.881 | 0.956 |
| champ-hard (dep<0.8) | 19 | 0.486 | **0.612** | 0.560 | 0.686 |

- On the champion's solved/partial parts Kimi is far behind — familiarity with the
  drawing conventions and part distribution is doing enormous work for the fine-tune.
- **On the champion's hard tail Kimi+loop is BETTER than the deployed policy**
  (0.612 vs 0.560) and close to the champion's own oracle (0.686). Kimi+loop solves the
  champion's single unsolved part (05f14712: 0.890 vs 0.000 across all 4 draws+repair)
  and passes the STaR 0.8 gate on **6 of the 19 champ-hard parts** (e.g. 0b611efc
  1.000 vs 0.631; 00199e66 0.976 vs 0.683).
- **Complementarity:** a hypothetical per-part max(kimi_agentic, champ_deployed) scores
  **0.919 — essentially the champion's oracle-of-4 ceiling (0.922)** without drawing
  extra champion samples.

## Variance probe — independent second run on 24 parts (`results_seed2.json`)

| arm | seed1 | seed2 | Δ |
|---|---|---|---|
| single-shot | 0.603 | 0.709 | +0.106 |
| agentic | 0.751 | 0.779 | +0.028 |

The loop damps draw noise at the mean level (±0.03, inside the project's ±0.03–0.05
seed-noise bar; single-shot swings ±0.11) but individual parts still swing hard
(5/24 moved >0.1, max 0.512 — 000bc5ac 0.453→0.965: seed2's turn-1 read the wall
correctly). STaR-gate yield 13/24 vs 15/24; union 16/24 — a second independent
loop run harvests meaningfully more accepted trajectories.

## Cost / latency — honest comparison

Kimi runs 1 attempt + loop; the champion runs 4 independent draws + repair. Per part:

| | Kimi single-shot | Kimi agentic | champ deployed bo4 |
|---|---|---|---|
| model calls | 1 | mean 2.62 (max 12) | 4 draws (+rare repair) |
| tokens | 4.1k in / 17.9k out | 25.3k in / 25.6k out | ≤4×2.4k out (27B local) |
| wall-clock | mean 589 s* | mean 697 s* | ~3.2 H200-min |

*Router wall-clock at 5-way concurrency sharing the hub with exp3; Kimi's own thinking
dominates (single calls of 24–48 min observed on hard parts). Whole run: 96 parts ≈ 9 h
at 5 workers ≈ 2.7 M in + 2.5 M out tokens. The champion evaluates the same pool in
~19 min on 16 H200 workers. As a *deployment* the fine-tune is orders of magnitude
cheaper per part; as a *teacher* Kimi's cost is paid once per accepted trajectory.

## Verdict — what this says about harness vs fine-tuning

1. **A frontier generalist + agentic harness does NOT substitute for task fine-tuning
   on-distribution.** Kimi+loop (0.724) sits below even the champion's greedy pass
   (0.787) and far below deployed best-of-4 (0.876) on the champion's benchmark. The
   loop reliably fixes *execution*; it cannot supply the drawing-convention fluency and
   dimension-reading priors the fine-tune absorbed from training data (worst failure
   class: misread dims and misidentified unlabeled views, defended to FINAL).
2. **The harness's value is orthogonal, not competitive.** +0.175 with zero regressions
   and 100% exec is exactly the property a data engine needs; and exp2 showed the same
   loop is worth +0.60 to the champion-class base model. Harness and fine-tuning
   compose: fine-tune for the distribution, loop for coverage and repair.
3. **As an RFT teacher, Kimi+loop earns its cost precisely where the champion is
   stuck.** It solves the champion's only unsolved part, beats deployed on the
   champ-hard bucket (0.612 vs 0.560), passes the STaR gate on 6/19 champ-hard parts,
   and max(kimi, champion) ≈ the champion's oracle ceiling (0.919 vs 0.922). A
   teacher run over the *training* pool's hard tail (+ a second seed, which lifted
   union yield 13→16/24) is the cheapest way rft_v3 can buy examples the champion
   cannot generate for itself — 45/96 accepted trajectories on the eval pool here,
   with plans that contain the explicit chain arithmetic rft_v3 wants to distill.
4. Caveats: Kimi ran 1 attempt+loop vs the champion's 4 draws (a 4-draw Kimi
   best-of-N was out of budget — at ~50k tokens/part/run it would cost ~10 M tokens
   and ~2 days of router time); per-part loop variance is large (max seed swing 0.51)
   even though the 96-part mean is stable to ~±0.03; and the router 502s/runaway
   thinking mean wall-clock numbers are upper bounds on a quiet router.

## Artifacts

- `results.json` (96 parts), `results_seed2.json` (24 parts) — per-part summaries incl.
  token accounting; committed.
- `trajectories/*.json` (+ `trajectories/seed2/`) — full turn-by-turn records (plan,
  code, measurements, usage, per-candidate IoU). `trajectories/accepted/` — 45 (seed1)
  + 15 (seed2) STaR-gate plan+code pairs.
- `artifacts/` (gitignored): drawings, per-candidate .py/.stl/.step/renders, run logs,
  `final_summary.txt`.
- `harness/`: prep_data.py, run_arms.py, summarize.py (+ exec_harness/iou/
  inspect_candidate copied verbatim from exp2).

## Reproduce

```bash
/software/python-3.11.1/bin/python3.11 harness/prep_data.py       # extract benchmark
python3 harness/run_arms.py --workers 5                            # main, resume-safe
python3 harness/run_arms.py --workers 4 --tag seed2 --limit 24     # variance probe
python3 harness/summarize.py                                       # analysis + tables
```

Hygiene: solver ran remotely via the router (shared politely with exp3, ≤5–6 in
flight); no GPUs on this box were touched; generated scripts executed in temp dirs
outside the repo.

## Appendix — per-sample table

(sorted by kimi_agentic − champ_deployed; full 96 rows)

| key | kimi ss | kimi ag | calls | champ greedy | champ dep | champ ora | ag−dep |
|---|---|---|---|---|---|---|---|
| 10a652e2-346 | 0.038 | 0.038 | 2 | 1.000 | 1.000 | 1.000 | -0.962 |
| 0e6d9ff8-bd0 | 0.000 | 0.146 | 5 | 0.961 | 0.961 | 0.961 | -0.815 |
| 0f58d446-836 | 0.154 | 0.201 | 3 | 0.951 | 0.951 | 0.957 | -0.750 |
| 04e95c60-20c | 0.196 | 0.196 | 2 | 0.928 | 0.928 | 0.928 | -0.732 |
| 10827958-85b | 0.091 | 0.091 | 3 | 0.778 | 0.778 | 0.778 | -0.687 |
| 07832ef6-5dd | 0.376 | 0.376 | 2 | 0.986 | 0.986 | 1.000 | -0.610 |
| 0024c6d8-aa7 | 0.000 | 0.398 | 3 | 1.000 | 1.000 | 1.000 | -0.602 |
| 067e685e-8e0 | 0.461 | 0.461 | 2 | 1.000 | 1.000 | 1.000 | -0.539 |
| 000bc5ac-ffb | 0.453 | 0.453 | 2 | 0.982 | 0.982 | 0.982 | -0.529 |
| 00874eac-be8 | 0.000 | 0.491 | 3 | 0.000 | 1.000 | 1.000 | -0.509 |
| 0a559fe2-ac3 | 0.228 | 0.228 | 2 | 0.701 | 0.701 | 0.833 | -0.473 |
| 07d2049a-e04 | 0.297 | 0.517 | 3 | 0.985 | 0.985 | 0.993 | -0.468 |
| 09ca4d7a-4a0 | 0.554 | 0.554 | 2 | 1.000 | 1.000 | 1.000 | -0.445 |
| 0d838d1e-2f5 | 0.541 | 0.541 | 3 | 0.966 | 0.966 | 0.990 | -0.425 |
| 0d9544aa-488 | 0.549 | 0.549 | 2 | 0.965 | 0.965 | 1.000 | -0.415 |
| 03dfa680-4b6 | 0.000 | 0.430 | 3 | 0.839 | 0.839 | 0.959 | -0.408 |
| 0b144460-77a | 0.000 | 0.417 | 3 | 0.820 | 0.820 | 1.000 | -0.403 |
| 0ae0be88-1a8 | 0.611 | 0.611 | 2 | 1.000 | 1.000 | 1.000 | -0.389 |
| 02042bd8-55d | 0.610 | 0.610 | 2 | 0.998 | 0.998 | 1.000 | -0.388 |
| 082dbea2-e3f | 0.625 | 0.625 | 2 | 1.000 | 1.000 | 1.000 | -0.375 |
| 0a7b7956-680 | 0.502 | 0.502 | 2 | 0.836 | 0.836 | 0.971 | -0.334 |
| 028bb3be-e82 | 0.596 | 0.596 | 2 | 0.927 | 0.927 | 0.994 | -0.332 |
| 0d4e9816-812 | 0.000 | 0.586 | 3 | 0.910 | 0.910 | 0.985 | -0.324 |
| 0cd10c0c-4f2 | 0.575 | 0.575 | 2 | 0.893 | 0.893 | 0.966 | -0.318 |
| 024cdfc2-289 | 0.000 | 0.554 | 3 | 0.870 | 0.870 | 0.962 | -0.316 |
| 05ede2e8-984 | 0.000 | 0.694 | 3 | 0.983 | 0.983 | 0.983 | -0.290 |
| 03fe9cac-607 | 0.000 | 0.670 | 4 | 0.954 | 0.954 | 0.960 | -0.284 |
| 0a0a5992-bf7 | 0.000 | 0.619 | 5 | 0.902 | 0.902 | 0.902 | -0.284 |
| 092593f2-bbb | 0.000 | 0.651 | 3 | 0.927 | 0.927 | 0.932 | -0.276 |
| 0f65741c-449 | 0.000 | 0.534 | 3 | 0.810 | 0.810 | 0.959 | -0.275 |
| 0b9e23e2-2da | 0.724 | 0.724 | 2 | 0.000 | 0.987 | 0.987 | -0.263 |
| 061ae590-e22 | 0.695 | 0.701 | 3 | 0.953 | 0.953 | 1.000 | -0.252 |
| 04e8b530-888 | 0.590 | 0.590 | 2 | 0.000 | 0.831 | 0.831 | -0.241 |
| 103a4b9c-3e8 | 0.707 | 0.707 | 2 | 0.941 | 0.941 | 0.954 | -0.235 |
| 0730e4f2-e95 | 0.705 | 0.705 | 2 | 0.930 | 0.930 | 1.000 | -0.225 |
| 0ee24452-202 | 0.749 | 0.749 | 2 | 0.971 | 0.971 | 0.971 | -0.222 |
| 0c43354e-b72 | 0.789 | 0.789 | 2 | 1.000 | 1.000 | 1.000 | -0.211 |
| 06b4e884-848 | 0.793 | 0.793 | 2 | 1.000 | 1.000 | 1.000 | -0.206 |
| 10d0ca90-0d1 | 0.788 | 0.788 | 2 | 0.994 | 0.994 | 0.994 | -0.206 |
| 090d59fe-be2 | 0.543 | 0.543 | 12 | 0.000 | 0.741 | 0.741 | -0.197 |
| 04a4e152-726 | 0.479 | 0.479 | 2 | 0.662 | 0.662 | 0.842 | -0.183 |
| 0fdd267e-0ea | 0.582 | 0.610 | 3 | 0.000 | 0.791 | 1.000 | -0.181 |
| 08734382-459 | 0.000 | 0.001 | 10 | 0.166 | 0.166 | 0.631 | -0.165 |
| 0cfc10be-e86 | 0.819 | 0.819 | 2 | 0.969 | 0.969 | 0.970 | -0.150 |
| 10dff308-8a8 | 0.864 | 0.864 | 2 | 1.000 | 1.000 | 1.000 | -0.136 |
| 014e0c04-50a | 0.875 | 0.875 | 2 | 1.000 | 1.000 | 1.000 | -0.125 |
| 0feed9be-4eb | 0.000 | 0.897 | 3 | 1.000 | 1.000 | 1.000 | -0.103 |
| 0eec11b2-ced | 0.752 | 0.889 | 4 | 0.000 | 0.988 | 0.988 | -0.100 |
| 0e134a30-6df | 0.912 | 0.912 | 2 | 1.000 | 1.000 | 1.000 | -0.088 |
| 01f125ec-6a2 | 0.834 | 0.834 | 2 | 0.919 | 0.919 | 0.919 | -0.085 |
| 01854fac-2b6 | 0.923 | 0.923 | 2 | 0.988 | 0.988 | 1.000 | -0.065 |
| 03b5b65e-5bd | 0.941 | 0.941 | 4 | 0.987 | 0.987 | 0.989 | -0.046 |
| 08ceb60e-09e | 0.000 | 0.955 | 3 | 1.000 | 1.000 | 1.000 | -0.045 |
| 0d2a56a4-4a6 | 0.765 | 0.765 | 2 | 0.805 | 0.805 | 0.945 | -0.040 |
| 07bfb06a-623 | 0.870 | 0.942 | 4 | 0.978 | 0.978 | 0.985 | -0.036 |
| 0580ef4e-eda | 0.386 | 0.386 | 2 | 0.416 | 0.416 | 0.416 | -0.030 |
| 07035802-864 | 0.903 | 0.903 | 2 | 0.929 | 0.929 | 1.000 | -0.026 |
| 05d7977c-c02 | 0.772 | 0.772 | 2 | 0.000 | 0.793 | 1.000 | -0.021 |
| 053ba312-304 | 0.926 | 0.926 | 2 | 0.947 | 0.947 | 0.962 | -0.021 |
| 0979b252-eee | 0.974 | 0.974 | 2 | 0.993 | 0.993 | 0.997 | -0.019 |
| 082d1e48-208 | 0.991 | 0.991 | 2 | 1.000 | 1.000 | 1.000 | -0.009 |
| 10d37114-259 | 0.992 | 0.992 | 2 | 1.000 | 1.000 | 1.000 | -0.008 |
| 042c25e6-40b | 0.954 | 0.954 | 2 | 0.958 | 0.958 | 0.986 | -0.004 |
| 0dd6ca4c-ec3 | 0.000 | 0.926 | 3 | 0.928 | 0.928 | 0.964 | -0.003 |
| 0a01a8f6-a78 | 0.998 | 0.998 | 2 | 1.000 | 1.000 | 1.000 | -0.002 |
| 00d1e3d6-db1 | 0.000 | 0.998 | 3 | 0.999 | 0.999 | 0.999 | -0.000 |
| 01bcfa42-0f4 | 1.000 | 1.000 | 2 | 1.000 | 1.000 | 1.000 | +0.000 |
| 0cb7362e-599 | 0.000 | 1.000 | 3 | 0.000 | 1.000 | 1.000 | +0.000 |
| 0d8231a8-81f | 1.000 | 1.000 | 2 | 1.000 | 1.000 | 1.000 | +0.000 |
| 0ead60ac-739 | 1.000 | 1.000 | 2 | 1.000 | 1.000 | 1.000 | +0.000 |
| 1027d3e0-b91 | 1.000 | 1.000 | 2 | 1.000 | 1.000 | 1.000 | +0.000 |
| 104587fa-61e | 1.000 | 1.000 | 2 | 1.000 | 1.000 | 1.000 | +0.000 |
| 0d6ee184-71d | 0.978 | 0.978 | 2 | 0.977 | 0.977 | 0.977 | +0.001 |
| 038de502-dae | 1.000 | 1.000 | 2 | 0.998 | 0.998 | 1.000 | +0.002 |
| 0975cab6-f02 | 0.996 | 0.996 | 2 | 0.992 | 0.992 | 0.992 | +0.004 |
| 0264f04e-987 | 0.985 | 0.985 | 2 | 0.000 | 0.979 | 0.983 | +0.007 |
| 02133c18-027 | 0.900 | 0.900 | 2 | 0.894 | 0.894 | 0.894 | +0.007 |
| 0f48f6f2-1b8 | 0.830 | 0.830 | 2 | 0.815 | 0.815 | 0.995 | +0.015 |
| 0cfca2a4-82f | 0.980 | 0.980 | 2 | 0.959 | 0.959 | 0.959 | +0.021 |
| 0a8774b8-ccb | 0.000 | 1.000 | 3 | 0.968 | 0.968 | 1.000 | +0.032 |
| 0120e88c-df7 | 0.992 | 0.992 | 3 | 0.959 | 0.959 | 0.994 | +0.033 |
| 0a3681ac-2be | 0.540 | 0.543 | 3 | 0.504 | 0.504 | 0.509 | +0.039 |
| 108abe88-f9f | 0.000 | 0.999 | 3 | 0.959 | 0.959 | 0.959 | +0.040 |
| 09a06a3c-9e5 | 0.000 | 0.746 | 3 | 0.698 | 0.698 | 0.712 | +0.048 |
| 0e14533a-a75 | 0.000 | 0.960 | 3 | 0.912 | 0.912 | 0.980 | +0.048 |
| 080b2e00-c9b | 0.877 | 0.877 | 2 | 0.808 | 0.808 | 0.965 | +0.069 |
| 058f2c3a-cfc | 0.824 | 0.824 | 2 | 0.739 | 0.739 | 0.998 | +0.084 |
| 09dc90de-9ef | 0.479 | 0.479 | 2 | 0.000 | 0.385 | 0.385 | +0.094 |
| 0ce4f582-33c | 0.980 | 0.980 | 2 | 0.816 | 0.816 | 0.968 | +0.164 |
| 087bbb7a-c87 | 0.973 | 0.973 | 2 | 0.787 | 0.787 | 0.996 | +0.185 |
| 02b4260a-2c8 | 1.000 | 1.000 | 2 | 0.798 | 0.798 | 1.000 | +0.202 |
| 00199e66-2f8 | 0.976 | 0.976 | 2 | 0.683 | 0.683 | 1.000 | +0.293 |
| 06e3334c-5c6 | 0.000 | 0.715 | 3 | 0.359 | 0.359 | 0.369 | +0.356 |
| 02c2c534-fdf | 0.365 | 0.365 | 2 | 0.000 | 0.000 | 0.048 | +0.365 |
| 0b611efc-c10 | 1.000 | 1.000 | 2 | 0.631 | 0.631 | 0.780 | +0.369 |
| 05f14712-467 | 0.000 | 0.890 | 3 | 0.000 | 0.000 | 0.000 | +0.890 |
