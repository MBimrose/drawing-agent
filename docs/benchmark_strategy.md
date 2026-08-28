# Larger-benchmark strategy (draft v1 — finalize with exp3–5 results)

Decides how to evaluate drawing→STEP systems beyond the frozen 96-sample eval and exp2's 20
fresh parts, with enough statistical power to rank strategies honestly against the cluster
fine-tuning practice.

## 1. The measured noise floor (from exp1 per-sample data, n=96)

| Quantity | Value |
|---|---|
| Per-sample IoU sd (deployed policy) | 0.203 |
| Per-sample sd, greedy | 0.332 |
| Per-sample sd of PAIRED deltas (oracle−deployed) | 0.083 |

Required n for a 95% CI half-width (mean IoU):

| Target resolution | Unpaired single-arm | Paired-by-part delta |
|---|---|---|
| ±0.01 | ~1,580 | ~265 |
| ±0.02 | ~395 | ~67 |
| ±0.03 | ~176 | ~30 |

Two consequences:
- **The frozen 96 can never resolve <±0.04 unpaired** — which is exactly the observed
  ±0.03–0.05 cross-run "seed noise". That noise is mostly sampling noise of a small pool, not
  training stochasticity.
- **Paired designs are ~6× cheaper.** Every A/B (policy vs policy, harness vs fine-tune,
  prompt vs prompt) must be paired on identical parts — and where possible on identical
  turn-1 candidates (the exp2 trick), which removes sampling noise from the delta entirely.

## 2. What the benchmark must stress

Evidence so far says difficulty lives in **dimension inference, not geometry**:
- cadgenbench: same part re-dimensioned indirectly → 0.93 → 0.63 (GPT-5.5).
- exp2: chained split costs Kimi single-shot −0.149 vs direct; the agentic loop recovers most.
- drawing-vlm corpus: 33% of sheets have unplaced dims (filtered out of training as noise —
  but they are a real difficulty axis, currently untested).

So stratify by **dimensioning scheme**, not just part family:
`direct` / `chained` (overalls suppressed) / `mixed` / `sparse` (a controlled dose of
required-value omission, solvable by convention defaults — the cadgenbench "named defaults"
regime). Keep family diversity as a secondary axis (exp2's 7 families + new ones incl.
revolved/axisymmetric and shelled parts, the known weak spots).

## 3. Options considered

**A. Keep only the frozen 96.** Continuity with e1→e27 history; zero build cost. But: top is
saturating (46/96 near-ties across draws), resolution floor above, single dimensioning style,
and it is the *training distribution's* eval — it cannot measure generalization to harder
dimensioning.

**B. Benchmark v2 — fresh generated, stratified, paired (RECOMMENDED).**
~240 parts: 4 dimensioning schemes × ~10 families × ~6 seeds, generated with the exp2
`gen/` machinery (controlled dimensioner + placed-dimension solvability check, 20/20 clean
in exp2). Authoring rules learned from drawing-vlm's scar tissue: GT code must execute at
authoring time (the v14 corpus is 21% exec-bad); GT meshes come from the STEP directly
(the v15 lesson); fresh string seeds → held out from all training by construction.
Power: paired ±~0.011 at n=240; unpaired ±~0.026. Report overall + per-scheme means,
paired bootstrap CIs (exp1 analyze_bo4.py machinery), and the STaR-gate yield (fraction
IoU≥0.8) as a first-class metric — it is what the data engine actually optimizes.
Cost: generation is local CPU (minutes); champion eval of 240 parts ≈ 1.2× the exp1 rerun
(~25 min on 16 H200); frontier arms are router-bound (~exp2 rates).

**C. External anchor.** A small subset scored with the real cadgenbench metric
(surface-distance F1 + volume IoU, pinned commit — see selfbench/local_score.py in pzfreo's
repo) to verify centered-IoU rankings transfer to an external metric; optionally a CADGenBench
submission later for outside validity. Not a per-experiment tool — a periodic sanity check.

## 4. Recommendation

Primary = **B** (240-part stratified v2, paired evaluation protocol). Keep **A** as a
continuity anchor reported alongside every major result (it is what all historical numbers
are on). Run **C** once after the first v2 cycle.

Protocol rules (non-negotiable, all learned the hard way):
1. Paired-by-part always; shared turn-1 candidates when comparing loop policies.
2. ≥2 seeds for any stochastic arm before believing a delta < 0.03.
3. No GT signal in any selection or feedback path of a deployable policy.
4. Never mix eval eras/pools in one table (the v14/v15 n=79/n=95 lesson).
5. Checkpoint/system selection by benchmark IoU, never by validation loss.

## 5. Open until exp3–5 land

- Which systems enter the v2 matrix (champion + best policy from exp3; champion-in-loop from
  exp5 if it beats 0.876; Kimi arms from exp4 as teacher reference).
- Whether STaR-gate yield or mean IoU is the headline column for data-engine decisions.
- Whether the sparse/underdetermined scheme is scoreable with centered IoU alone or needs a
  dimensional-accuracy metric (per-dimension relative error extracted from the GT parameter
  table — the generator knows every named parameter, so this is cheap to add).
