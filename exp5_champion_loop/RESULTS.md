# Exp 5 results — the fine-tuned champion inside the measurement-feedback loop

**Date:** 2026-08-28 · **Eval:** frozen 96-sample pool, centered volumetric IoU vs
`gt_meshes_v15` · **Model:** e24-rft `consolidated-checkpoint-3250` (the exp1 weights,
HF `generate`, exp1's pinned env) · **Compute:** 16 single-H200 workers on
wpk-serv-05 + 06, 9.8 min max wall, **1.06 GPU-h**.

## TL;DR

| Policy | Mean centered IoU |
|---|---|
| greedy turn-1 (= exp1 draw 0, bit-exact parity) | **0.7871** |
| **champion + measurement loop (this exp)** | **0.8178** |
| champion + loop, keep-best-seen | 0.8179 |
| deployed best-of-4 + repair (exp1) | 0.8756 |
| oracle-of-4 (exp1) | 0.9222 |

**The loop does NOT add IoU on top of fine-tuning + best-of-4 + repair.** It beats its
own greedy turn-1 by +0.031 (paired CI [+0.000, +0.071] — marginal), but lands **−0.058
below the deployed best-of-4 policy** [CI −0.106, −0.016] and −0.104 below the oracle.
The decomposition says exactly why, and it is structural, not a tuning accident:

- On the **84 samples whose turn-1 executes** (where deployed = greedy by construction),
  the loop contributes **+0.0003**: one real refinement (+0.034), three ~−0.003
  regressions, everything else byte-identical re-emission or instant FINAL.
- On the **12 turn-1 exec failures**, conditioned repair rescues **4/12** (mean IoU
  0.244) where the deployed policy's *fresh* draws rescue **11/12** (mean 0.708).
  That single difference is −0.058 of the 96-sample mean — the entire deficit.

**Verdict: for this RFT-sharpened champion, the agentic loop is not additive with
best-of-4 — it is a strictly worse substitute for it.** Fine-tuning + fresh-draw
sampling already banks everything the loop could offer, and the loop's one lever the
bo4 policy lacks (post-exec revision) fires once in 84 opportunities. The remaining
0.876 → 0.922 gap stays what exp1 said it was: a *selection* problem (critic), not a
*revision* problem.

## Method

Turn 1 = greedy generation with the training prompts — verified **bit-exact against
exp1's draw 0** (median AND max |ΔIoU| = 0.000000 at the summary's 6-decimal precision,
same batch composition per worker). Then up to 8 feedback rounds per sample:

- exec failure → the vendored deployed-repair feedback (stderr tail);
- exec success → measurements of the model's own solid (bbox / volume / solid+face
  census / cylindrical radii) **plus a Top/Front/Right line-render image** of its
  candidate, and a re-derivation checklist (re-read dims from scratch, per-axis chain
  arithmetic, compare vs measured bbox/radii/renders) ending in "corrected script or
  FINAL". No ground truth, no verdicts anywhere.
- Final answer = last executing candidate (checkpoint-first). Stops: FINAL /
  convergence / 2× no-code / budget.

**Multi-image works.** The champion's chat template and processor accept a render PNG in
mid-conversation user turns (only the newest render stays an image); generation stays
coherent. No text-only fallback was needed — renders were ON for the full run.

Three design decisions forced by smoke tests (all on the record in PLAN.md):

1. **Greedy feedback rounds are degenerate** — the champion regenerates byte-identical
   code from identical feedback, even for broken scripts with the traceback in context.
   Rounds ≥1 therefore sample at **T=0.7/top-p 0.95 — exactly the deployed bo4 draw
   settings**, so loop rounds and bo4 draws spend the same kind of compute.
2. **A soft "revise if needed" invitation is a free exit**: every mediocre executing
   sample (IoU 0.17–0.63!) replied FINAL after one round, re-asserting its own reading.
   The checklist feedback closes that exit — after which the model re-emits its
   previous script **byte-identically at T=0.7** instead. Same outcome, more honest
   stop label.
3. **Convergence stop applies only to executing candidates** (run v2). In v1 it also
   stopped broken chains on identical re-emission, cutting them at 1–2 attempts
   (v1 final: 0.8122, 4/12 rescues). v2 gives broken chains the full budget; they used
   all 9 calls. v1 is kept as the strict-stop ablation (`loop_summary_v1.json`).

## The paired numbers (n = 96, same turn-1 as exp1's draw 0)

| Gap | Mean | Bootstrap 95% CI |
|---|---|---|
| loop final − greedy | +0.0307 | [+0.0002, +0.0711] |
| loop final − deployed bo4+repair | **−0.0577** | [−0.1064, −0.0162] |
| loop final − oracle-of-4 | −0.1043 | [−0.1553, −0.0606] |
| loop best-seen − greedy | +0.0308 | [+0.0004, +0.0712] |

Keep-best ≈ final: only 3 samples finished below their best-seen (mean gap 0.003) — with
the exec-only convergence stop, "trust the last executing candidate" is sound. (In v1 a
single wander cost one sample 0.662 → 0.141; the fixed stop rule removed it.)

### Where the loop's +0.031 comes from — and where the −0.058 goes

**Rescues (4/12).** 0eec11b2 0→0.988, 04e8b530 0→0.972, 0fdd267e 0→0.967 (both *above*
their deployed values — conditioned repair, when it works, can beat a fresh draw), and
02c2c534 0→executes-but-0.000 (= its deployed outcome). The other **8 failures burned
all 9 calls without ever producing an executing script**: 9 candidates each containing
only 1–4 distinct scripts, all dying on the same chamfer/fillet/boolean errors
(`Failed creating a chamfer, try a smaller length` etc.). Conditioned on its own broken
code, the champion keeps the broken approach; the deployed policy's *fresh independent
draws* de-anchor it — that is why bo4 rescued 11/12 (deployed mean on these 12: 0.708
vs the loop's 0.244; ×12/96 = the −0.058 deficit). Rescue identity is also a coin flip:
0cb7362e was rescued at ~0.97 in v1 and both smokes, missed in all 9 v2 attempts.

**Refinement (1/84).** 0d9544aa: 0.965 → 0.974 → 0.999 across two measurement rounds,
then converged — beats its deployed 0.965, essentially reaches its oracle 1.000. This is
the loop working exactly as designed. It happened once. Three regressions of ~−0.003
round it out; the other 80 executing samples either FINAL'd (59 overall) or re-emitted
their script byte-identically (converged, 29).

**Cost.** Mean 2.81 calls/sample (median 2), total 1.06 GPU-h vs ~5.1 GPU-h for exp1's
all-draws rerun (a production early-stop bo4 policy is ~1.5 GPU-h). The loop is cheap —
just not effective.

## STaR / data-engine angle (the exp2 question at champion scale)

Gate yield (IoU ≥ 0.8): **greedy 71/96 → loop-final 74/96** (+3 = exactly the three
good rescues; best-seen also 74). And since 80/84 executing samples end on their turn-1
script verbatim, the loop's accepted set is ≈ the greedy accepted set plus three
repair trajectories. **Using the champion itself as an agentic rft_v3 generator adds
almost nothing over plain greedy/temperature sampling** — the polar opposite of exp2's
base-model result (single-shot 0/20 → loop 9/20 on fresh drawings). The data-engine
value of the loop lives in weak/pre-RFT policies; RFT itself consumes the head-room the
loop needs. (Corollary: successive STaR rounds make the loop *less* useful as a
generator, not more.)

## Why the champion won't revise (and what would actually stack)

The champion is mode-collapsed by RFT: conditioned on its own answer — even with
measurements, a self-render, stderr, and an explicit checklist in context — its T=0.7
posterior re-emits that answer byte-for-byte. Feedback about its OWN part cannot
contradict a wrong belief about the TARGET (exp2's blind spot, now confirmed on the
frozen pool); and unlike exp2's Kimi/base-qwen, it doesn't even engage with exec
errors it "believes" in (8/12 chains never deviated from the broken construction).

What this implies for the pipeline:

1. **Keep best-of-4 fresh draws as the coverage mechanism.** Nothing here replaces it;
   conditioned repair is a worse rescue channel than one fresh draw (4/12 vs 8/12 on
   draw 1 alone in exp1).
2. **A loop pass stacked ON TOP of deployed bo4 would add ≈ +0.000–0.003** (the
   84-sample executing delta) — not worth 2.8 calls/sample. Don't build it.
3. **The 0.876 → 0.922 oracle gap remains a selection problem.** exp1's qualified GO
   for a critic/reranker (gross-error detection on executing candidates) is unchanged
   and is the only measured path to the oracle; this experiment eliminates "agentic
   revision" as the alternative route.
4. If an agentic harness is ever wanted for this champion, its exec-failure branch
   should issue a **fresh redraw (no previous code in context)** rather than
   conditioned repair — that single change is worth ~+0.05 mean on this pool.

## Artifacts

- `loop_summary.json` (committed) — per-sample paired rows (v2, headline).
- `loop_summary_v1.json` (committed) — strict-convergence-stop ablation (0.8122).
- `artifacts/shards{,_v1}/loop_w*.json` (gitignored) — full records: per-round code,
  exec/stderr, measurements, IoU; also on both nodes under
  `/srv/scratch/bimrose2/drawing_agent_exp5/out_loop{,_v1}/` with candidate
  .py/.stl/.step and render PNGs in `candidates/`.
- Smokes under `.../drawing_agent_exp5/out_smoke{,2,3}/` (parity, FINAL-exit and
  convergence behavior).
- GPUs on both nodes verified released after the runs.

## Reproduce

```bash
# on each node (serv-06: base 0, serv-05: base 8):
bash exp5_champion_loop/run_node.sh 0 16 on
# merge + analyze:
python3 exp5_champion_loop/analyze_loop.py .../out_loop/loop_w*.json \
    --bo4 exp1_bestof4_oracle/bo4_oracle_summary.json --summary loop_summary.json
```

## Appendix — per-sample table

(turn-1 = greedy draw 0; Δloop = loop final − turn-1; deployed/oracle from exp1;
sorted by Δloop; rd = round of the candidate)

| key | turn-1 | loop final (rd) | best (rd) | Δloop | deployed | oracle | stop |
|---|---|---|---|---|---|---|---|
| 0eec11b2-ced | 0.000 | 0.988 (2) | 0.988 (1) | +0.988 | 0.988 | 0.988 | converged |
| 04e8b530-888 | 0.000 | 0.972 (3) | 0.972 (3) | +0.972 | 0.831 | 0.831 | final |
| 0fdd267e-0ea | 0.000 | 0.967 (5) | 0.967 (5) | +0.967 | 0.791 | 1.000 | final |
| 0d9544aa-488 | 0.965 | 0.999 (3) | 0.999 (2) | +0.034 | 0.965 | 1.000 | converged |
| 000bc5ac-ffb | 0.982 | 0.982 (0) | 0.982 (0) | +0.000 | 0.982 | 0.982 | final |
| 00199e66-2f8 | 0.683 | 0.683 (1) | 0.683 (0) | +0.000 | 0.683 | 1.000 | converged |
| 0024c6d8-aa7 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 00874eac-be8 | 0.000 | 0.000 (None) | 0.000 (None) | +0.000 | 1.000 | 1.000 | budget |
| 00d1e3d6-db1 | 0.999 | 0.999 (0) | 0.999 (0) | +0.000 | 0.999 | 0.999 | final |
| 0120e88c-df7 | 0.959 | 0.959 (0) | 0.959 (0) | +0.000 | 0.959 | 0.994 | final |
| 014e0c04-50a | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 01854fac-2b6 | 0.988 | 0.988 (0) | 0.988 (0) | +0.000 | 0.988 | 1.000 | final |
| 01bcfa42-0f4 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 01f125ec-6a2 | 0.919 | 0.919 (1) | 0.919 (0) | +0.000 | 0.919 | 0.919 | converged |
| 02042bd8-55d | 0.998 | 0.998 (0) | 0.998 (0) | +0.000 | 0.998 | 1.000 | final |
| 02133c18-027 | 0.894 | 0.894 (0) | 0.894 (0) | +0.000 | 0.894 | 0.894 | final |
| 024cdfc2-289 | 0.870 | 0.870 (1) | 0.870 (0) | +0.000 | 0.870 | 0.962 | converged |
| 0264f04e-987 | 0.000 | 0.000 (None) | 0.000 (None) | +0.000 | 0.979 | 0.983 | budget |
| 028bb3be-e82 | 0.927 | 0.927 (1) | 0.927 (0) | +0.000 | 0.927 | 0.994 | converged |
| 02b4260a-2c8 | 0.798 | 0.798 (0) | 0.798 (0) | +0.000 | 0.798 | 1.000 | final |
| 02c2c534-fdf | 0.000 | 0.000 (5) | 0.000 (4) | +0.000 | 0.000 | 0.048 | converged |
| 038de502-dae | 0.998 | 0.998 (0) | 0.998 (0) | +0.000 | 0.998 | 1.000 | final |
| 03b5b65e-5bd | 0.987 | 0.987 (0) | 0.987 (0) | +0.000 | 0.987 | 0.989 | final |
| 03dfa680-4b6 | 0.839 | 0.839 (0) | 0.839 (0) | +0.000 | 0.839 | 0.959 | final |
| 03fe9cac-607 | 0.954 | 0.954 (1) | 0.954 (0) | +0.000 | 0.954 | 0.960 | converged |
| 042c25e6-40b | 0.958 | 0.958 (0) | 0.958 (0) | +0.000 | 0.958 | 0.986 | final |
| 04a4e152-726 | 0.662 | 0.662 (0) | 0.662 (0) | +0.000 | 0.662 | 0.842 | final |
| 04e95c60-20c | 0.928 | 0.928 (0) | 0.928 (0) | +0.000 | 0.928 | 0.928 | final |
| 04e95c60-20c | 0.928 | 0.928 (0) | 0.928 (0) | +0.000 | 0.928 | 0.928 | final |
| 053ba312-304 | 0.947 | 0.947 (1) | 0.947 (0) | +0.000 | 0.947 | 0.962 | converged |
| 0580ef4e-eda | 0.416 | 0.416 (2) | 0.416 (0) | +0.000 | 0.416 | 0.416 | converged |
| 058f2c3a-cfc | 0.739 | 0.739 (1) | 0.739 (0) | +0.000 | 0.739 | 0.998 | converged |
| 05d7977c-c02 | 0.000 | 0.000 (None) | 0.000 (None) | +0.000 | 0.793 | 1.000 | budget |
| 05ede2e8-984 | 0.983 | 0.983 (0) | 0.983 (0) | +0.000 | 0.983 | 0.983 | final |
| 05f14712-467 | 0.000 | 0.000 (None) | 0.000 (None) | +0.000 | 0.000 | 0.000 | budget |
| 061ae590-e22 | 0.953 | 0.953 (0) | 0.953 (0) | +0.000 | 0.953 | 1.000 | final |
| 067e685e-8e0 | 1.000 | 1.000 (1) | 1.000 (0) | +0.000 | 1.000 | 1.000 | converged |
| 06b4e884-848 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 06e3334c-5c6 | 0.359 | 0.359 (0) | 0.359 (0) | +0.000 | 0.359 | 0.369 | final |
| 07035802-864 | 0.929 | 0.929 (1) | 0.929 (0) | +0.000 | 0.929 | 1.000 | converged |
| 0730e4f2-e95 | 0.930 | 0.930 (0) | 0.930 (0) | +0.000 | 0.930 | 1.000 | final |
| 07bfb06a-623 | 0.978 | 0.978 (1) | 0.978 (0) | +0.000 | 0.978 | 0.985 | converged |
| 07d2049a-e04 | 0.985 | 0.985 (0) | 0.985 (0) | +0.000 | 0.985 | 0.993 | final |
| 080b2e00-c9b | 0.808 | 0.808 (0) | 0.808 (0) | +0.000 | 0.808 | 0.965 | final |
| 082d1e48-208 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 082dbea2-e3f | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 08734382-459 | 0.166 | 0.166 (2) | 0.166 (0) | +0.000 | 0.166 | 0.631 | converged |
| 087bbb7a-c87 | 0.787 | 0.787 (1) | 0.787 (0) | +0.000 | 0.787 | 0.996 | converged |
| 08ceb60e-09e | 1.000 | 1.000 (2) | 1.000 (0) | +0.000 | 1.000 | 1.000 | converged |
| 090d59fe-be2 | 0.000 | 0.000 (None) | 0.000 (None) | +0.000 | 0.741 | 0.741 | budget |
| 092593f2-bbb | 0.927 | 0.927 (0) | 0.927 (0) | +0.000 | 0.927 | 0.932 | final |
| 0975cab6-f02 | 0.992 | 0.992 (1) | 0.992 (0) | +0.000 | 0.992 | 0.992 | converged |
| 0979b252-eee | 0.993 | 0.993 (1) | 0.993 (0) | +0.000 | 0.993 | 0.997 | final |
| 09a06a3c-9e5 | 0.698 | 0.698 (0) | 0.698 (0) | +0.000 | 0.698 | 0.712 | final |
| 09ca4d7a-4a0 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 09dc90de-9ef | 0.000 | 0.000 (None) | 0.000 (None) | +0.000 | 0.385 | 0.385 | budget |
| 0a01a8f6-a78 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 0a0a5992-bf7 | 0.902 | 0.902 (0) | 0.902 (0) | +0.000 | 0.902 | 0.902 | final |
| 0a3681ac-2be | 0.504 | 0.504 (0) | 0.504 (0) | +0.000 | 0.504 | 0.509 | final |
| 0a559fe2-ac3 | 0.701 | 0.701 (0) | 0.701 (0) | +0.000 | 0.701 | 0.833 | final |
| 0a7b7956-680 | 0.836 | 0.836 (0) | 0.836 (0) | +0.000 | 0.836 | 0.971 | final |
| 0a8774b8-ccb | 0.968 | 0.968 (0) | 0.968 (0) | +0.000 | 0.968 | 1.000 | final |
| 0ae0be88-1a8 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 0b144460-77a | 0.820 | 0.820 (0) | 0.820 (0) | +0.000 | 0.820 | 1.000 | final |
| 0b9e23e2-2da | 0.000 | 0.000 (None) | 0.000 (None) | +0.000 | 0.987 | 0.987 | budget |
| 0c43354e-b72 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 0cb7362e-599 | 0.000 | 0.000 (None) | 0.000 (None) | +0.000 | 1.000 | 1.000 | budget |
| 0cd10c0c-4f2 | 0.893 | 0.893 (0) | 0.893 (0) | +0.000 | 0.893 | 0.966 | final |
| 0ce4f582-33c | 0.816 | 0.816 (1) | 0.816 (0) | +0.000 | 0.816 | 0.968 | converged |
| 0cfc10be-e86 | 0.969 | 0.969 (1) | 0.969 (0) | +0.000 | 0.969 | 0.970 | converged |
| 0cfca2a4-82f | 0.959 | 0.959 (0) | 0.959 (0) | +0.000 | 0.959 | 0.959 | final |
| 0d2a56a4-4a6 | 0.805 | 0.805 (0) | 0.805 (0) | +0.000 | 0.805 | 0.945 | final |
| 0d4e9816-812 | 0.910 | 0.910 (0) | 0.910 (0) | +0.000 | 0.910 | 0.985 | final |
| 0d6ee184-71d | 0.977 | 0.977 (0) | 0.977 (0) | +0.000 | 0.977 | 0.977 | final |
| 0d8231a8-81f | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 0d838d1e-2f5 | 0.966 | 0.966 (0) | 0.966 (0) | +0.000 | 0.966 | 0.990 | final |
| 0dd6ca4c-ec3 | 0.928 | 0.928 (1) | 0.928 (0) | +0.000 | 0.928 | 0.964 | converged |
| 0e134a30-6df | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 0e6d9ff8-bd0 | 0.961 | 0.961 (0) | 0.961 (0) | +0.000 | 0.961 | 0.961 | final |
| 0ead60ac-739 | 1.000 | 1.000 (1) | 1.000 (0) | +0.000 | 1.000 | 1.000 | converged |
| 0ee24452-202 | 0.971 | 0.971 (0) | 0.971 (0) | +0.000 | 0.971 | 0.971 | final |
| 0f48f6f2-1b8 | 0.815 | 0.815 (0) | 0.815 (0) | +0.000 | 0.815 | 0.995 | final |
| 0f58d446-836 | 0.951 | 0.951 (1) | 0.951 (0) | +0.000 | 0.951 | 0.957 | converged |
| 0f65741c-449 | 0.810 | 0.810 (1) | 0.810 (0) | +0.000 | 0.810 | 0.959 | converged |
| 0feed9be-4eb | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 1027d3e0-b91 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 103a4b9c-3e8 | 0.941 | 0.941 (1) | 0.941 (0) | +0.000 | 0.941 | 0.954 | converged |
| 104587fa-61e | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 10827958-85b | 0.778 | 0.778 (1) | 0.778 (0) | +0.000 | 0.778 | 0.778 | converged |
| 108abe88-f9f | 0.959 | 0.959 (1) | 0.959 (0) | +0.000 | 0.959 | 0.959 | converged |
| 10a652e2-346 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 10d0ca90-0d1 | 0.994 | 0.994 (0) | 0.994 (0) | +0.000 | 0.994 | 0.994 | final |
| 10d37114-259 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 | 1.000 | 1.000 | final |
| 10dff308-8a8 | 1.000 | 1.000 (1) | 1.000 (0) | +0.000 | 1.000 | 1.000 | converged |
| 0e14533a-a75 | 0.912 | 0.909 (2) | 0.912 (0) | -0.003 | 0.912 | 0.980 | converged |
| 07832ef6-5dd | 0.986 | 0.982 (1) | 0.986 (0) | -0.003 | 0.986 | 1.000 | final |
| 0b611efc-c10 | 0.631 | 0.627 (1) | 0.631 (0) | -0.004 | 0.631 | 0.780 | final |
