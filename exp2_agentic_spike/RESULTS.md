# Exp 2 — Agentic-harness spike: results

**Headline: the agentic loop beats single-shot with the SAME model on the same
drawings — Kimi K3: 0.738 → 0.856 mean centered IoU (+0.118 overall; +0.149 on
indirectly-dimensioned "hard" parts, +0.087 on standard parts), exec success
17/20 → 20/20, at a mean cost of 2.3 model calls and ~8% extra wall-clock per
part; the loop never regressed a part. On a champion-class solver (qwen3.8-27b,
the drawing-vlm base) the effect is decisive: 0.128 → 0.728 (+0.600), exec 5/20
→ 20/20, STaR-gate (IoU ≥ 0.8) yield 0/20 → 9/20. Verdict: the agentic data
engine is justified.**

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

| part | split | single-shot IoU | agentic IoU | delta | model calls | stop | t_ss (s) | t_agentic (s) |
|---|---|---|---|---|---|---|---|---|
| std00_steps3 | std | 1.000 | 1.000 | +0.000 | 2 | final | 110 | 115 |
| std01_steps3 | std | 1.000 | 1.000 | +0.000 | 2 | final | 18 | 24 |
| std02_notchplate | std | 0.971 | 0.971 | +0.000 | 2 | final | 48 | 54 |
| std03_notchplate | std | 0.965 | 0.970 | +0.005 | 3 | final | 51 | 95 |
| std04_tblock | std | 0.000 | 0.860 | **+0.860** | 4 | final | 397 | 412 |
| std05_shaft | std | 0.839 | 0.839 | +0.000 | 2 | final | 304 | 310 |
| std06_shaft | std | 0.993 | 0.993 | +0.000 | 2 | final | 303 | 308 |
| std07_lbracket | std | 0.869 | 0.869 | +0.000 | 2 | final | 133 | 139 |
| std08_uchannel | std | 0.489 | 0.489 | +0.000 | 2 | final | 119 | 125 |
| std09_bossplate | std | 1.000 | 1.000 | +0.000 | 2 | final | 27 | 33 |
| hard00_steps3 | hard | 0.000 | 1.000 | **+1.000** | 3 | final | 78 | 91 |
| hard01_steps3 | hard | 0.000 | 0.483 | **+0.483** | 3 | final | 178 | 194 |
| hard02_notchplate | hard | 0.989 | 0.989 | +0.000 | 2 | final | 140 | 147 |
| hard03_notchplate | hard | 0.975 | 0.975 | +0.000 | 2 | final | 168 | 176 |
| hard04_tblock | hard | 1.000 | 1.000 | +0.000 | 2 | final | 124 | 131 |
| hard05_tblock | hard | 0.644 | 0.644 | +0.000 | 2 | final | 42 | 48 |
| hard06_shaft | hard | 0.940 | 0.940 | +0.000 | 2 | final | 39 | 47 |
| hard07_shaft | hard | 0.942 | 0.942 | +0.000 | 2 | final | 93 | 98 |
| hard08_lbracket | hard | 0.997 | 1.000 | +0.003 | 3 | final | 55 | 73 |
| hard09_uchannel | hard | 0.149 | 0.149 | +0.000 | 2 | final | 83 | 88 |

(agentic best-turn IoU == agentic final IoU on every part: the model's FINAL
choice never left a better intermediate behind. All 20 parts stopped on an
explicit FINAL — none hit the 12-call budget.)

## Split means — Kimi K3

| split | n | single-shot | agentic | delta | ss exec | ag exec | mean calls | mean t_ss | mean t_ag |
|---|---|---|---|---|---|---|---|---|---|
| std (direct dims) | 10 | 0.813 | 0.899 | **+0.087** | 9/10 | 10/10 | 2.3 | 151 s | 162 s |
| hard (chained dims) | 10 | 0.664 | 0.812 | **+0.149** | 8/10 | 10/10 | 2.3 | 100 s | 109 s |
| ALL | 20 | 0.738 | 0.856 | **+0.118** | 17/20 | 20/20 | 2.3 | 125 s | 135 s |

### Where the lift comes from (Kimi)

- **Execution repair (the whole story, essentially).** 3/20 turn-1 attempts
  produced no usable solid: 2 exec errors (`export_step` on the builder object;
  a Locations/align slip) and 1 runaway-`<think>` that burned 30k output tokens
  without ever emitting a code fence. The loop repaired all three in 1–2
  feedback rounds (+1.000, +0.860, +0.483). This is the same coverage
  phenomenon the drawing-vlm best-of-4 policy exploits — but the loop got
  20/20 exec vs 17/20, deterministically, with stderr-guided fixes instead of
  resampling.
- **Refinement is real but tiny when the code runs.** Only 2 executed parts
  improved (+0.005 hole-depth fix seen in the self-render; +0.003 polish).
- **The loop does NOT fix confident misreads.** All five residual misses are
  dimension-reading errors the model then defended to FINAL in one round:
  hard05 (0.644) and hard09 (0.149) both summed their chain **one-sided** —
  17+29 instead of 17+29+17 → X=46 vs 63; 9+42 instead of 9+42+9 → X=51 vs 60
  plus the same slip in Z — exactly the symmetric-segment trap of indirect
  dimensioning; std08 (0.489) invented a 63 mm height on a sheet that prints 39
  twice (its Right view is partially overlapped by the ISO view — renderer
  quirk); std05 (0.839) misread one shaft section length (Z 70 vs 77); std07
  (0.869) got the exact bbox but a feature (hole/thickness) wrong. In every
  case the model rebuilt a self-consistent part, compared its own render to the
  drawing, saw what it expected, and declared FINAL. Measurements of your OWN
  part cannot flag a wrong belief about the TARGET; that needs a sharper
  comparison signal (render/drawing overlay-diff, or an independent critic
  re-reading the drawing).
- **Hard split is genuinely harder single-shot** (0.664 vs 0.813; excluding
  exec failures 0.830 vs 0.903) — chained dimensioning costs Kimi ~0.07 IoU on
  executed parts, and both catastrophic misreads (hard09 0.149, hard05 0.644)
  are chained parts. Direction matches the cadgenbench finding, magnitude
  smaller (Kimi chains competently: e.g. it summed 28+21+17=66 in its plan).

## Secondary run — qwen3.8-27b (drawing-vlm base), fair output budget (24k)

Same 20 drawings, same prompts, same two arms, `--max-tokens 24000`
(`artifacts/results_qwen38b.json`):

| split | n | single-shot | agentic | delta | ss exec | ag exec | mean calls | mean t_ss | mean t_ag |
|---|---|---|---|---|---|---|---|---|---|
| std | 10 | 0.101 | 0.708 | **+0.607** | 2/10 | 10/10 | 4.2 | 210 s | 407 s |
| hard | 10 | 0.155 | 0.748 | **+0.592** | 3/10 | 10/10 | 4.4 | 184 s | 423 s |
| ALL | 20 | 0.128 | 0.728 | **+0.600** | 5/20 | 20/20 | 4.3 | 197 s | 415 s |

For the weaker, champion-class model the loop is not an increment — it is the
difference between a broken pipeline and a working one:

- **Single-shot passes the STaR 0.8 acceptance gate on 0/20 parts; agentic on
  9/20.** Turn-1 code almost always fails to execute (build123d API slips,
  runaway `<think>`); the loop repairs execution on all 20 and then keeps
  improving.
- **Genuine geometry refinement, not just exec repair**: hard01 0.389 → 1.000,
  hard05 0.515 → 1.000 (qwen+loop fully solved the symmetric-chain part that
  Kimi confidently got wrong at 0.644), hard06 0 → 0.989, hard07 0 → 1.000,
  std07 0 → 0.981, std06 0 → 0.945 — several of these took 3–5 feedback rounds
  of comparing its own re-render against the drawing.
- One regression, −0.007 (std08): the weak model revised a mediocre candidate
  into a marginally worse one and FINAL'd. Per-candidate scoring shows
  final ≈ best on every part (max gap 0.007), so "trust the model's FINAL" is a
  sound stopping rule even for the weak solver.
- Cost: 4.3 calls and 2.1× single-shot wall-clock per part.

### Footnote — output-budget sensitivity (first qwen run, 8k)

The first qwen run (`artifacts/results_qwen38.json`, max_tokens 8000 → router
delivered exactly 7600 output tokens/call) had turn 1 truncate mid-`<think>`
on 19/20 parts: single-shot 0.026 / exec 1/20, agentic 0.420 / exec 12/20, and
8 parts died on three consecutive no-code replies. Two lessons: (a) thinking
models need a large completion budget before "single-shot capability" is even
measurable; (b) even budget-starved, the loop quadrupled usable output — extra
turns partially substitute for missing thinking budget.

## Deliverables

- `artifacts/results.json` (Kimi), `results_qwen38b.json`, `results_qwen38.json`
  — per-part records; `harness/summarize.py` renders the tables above.
- `trajectories/*.json` — full turn-by-turn trajectories (plan, code, per-turn
  measurements, usage, per-candidate IoU) for every part and both models
  (`trajectories/qwen38b/` for the secondary).
- `trajectories/accepted/` — STaR-gate (IoU ≥ 0.8) plan+code pairs: **16/20
  Kimi**, 9/20 qwen38b. Plans contain explicit chain arithmetic ("X is given
  only as a component chain: 28 + 21 + 17 = 66") — precisely the reasoning
  rft_v3 wants to distill.
- Dataset (drawings + GT code/STEP/STL + placed-dimension inventories) under
  `artifacts/` (gitignored, regenerable via `gen/generate_dataset.py`).

## Verdict — is an agentic data engine for the STaR loop justified?

**Yes.** Three findings, in order of importance:

1. **For the champion-class model the loop is the pipeline.** On the
   drawing-vlm base model the acceptance-gate yield went 0/20 → 9/20 (+0.600
   mean IoU). A STaR engine that samples single-shot from a base/weak policy
   harvests almost nothing from fresh drawing families; the same policy inside
   the loop produces accepted trajectories at a usable rate, including full
   solves of indirect-dimensioned parts. The trajectories also embed the
   *process* (chain arithmetic, feedback-driven revision) rather than just the
   answer.
2. **For a strong teacher the loop is cheap insurance with a real tail win.**
   Kimi: +0.118 mean, entirely from rescuing the 3/20 turn-1 failures
   (+1.000/+0.860/+0.483), 0 regressions, 2.3 calls, +8% wall-clock. On the
   hard (indirect) split the delta is larger (+0.149 vs +0.087) — the question
   the experiment was asked. But on parts whose turn-1 code already executed,
   refinement gains were ≤0.005 — a strong model rarely revises its reading.
3. **The loop's blind spot is confident misreads, and it is structural.** Every
   residual Kimi miss (5 parts, incl. both one-sided chain sums 17+29 vs
   17+29+17) survived because measurements/self-renders of your OWN part cannot
   contradict a wrong belief about the TARGET. The fix is a sharper comparison
   signal: render-vs-drawing overlay diff, or an independent critic that
   re-reads the drawing (ties directly into exp1's critic-reranker question).

**Recommendation for rft_v3**: build the agentic engine with the exact feedback
stack used here (exec + stderr, bbox/volume/face measurements phrased as
numbers not verdicts, one self-render per turn), gate acceptance on GT IoU ≥
0.8 *outside* the loop, and add an overlay/critic comparison signal to attack
the misread tail. Expected cost at Kimi-teacher quality: ~2.3 calls/part;
at champion quality: ~4.3 calls/part for a yield single-shot cannot deliver
at all.

## Reproduce

```bash
# dataset (20 parts + drawings), system python 3.11 w/ build123d 0.10:
/software/python-3.11.1/bin/python3.11 gen/generate_dataset.py
# arms:
python3 harness/run_arms.py --workers 5                                   # Kimi
python3 harness/run_arms.py --workers 10 --model claude-qwen3.8-27b \
        --tag qwen38b --max-tokens 24000                                  # secondary
python3 harness/summarize.py [artifacts/results_qwen38b.json]
```

Hygiene: solver ran remotely via the router; no VL server was launched on
wpk-serv-06 and its GPUs were never touched by this experiment.


*(pending)*
