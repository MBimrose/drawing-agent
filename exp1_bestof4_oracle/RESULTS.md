# Exp 1 results — Best-of-4 oracle gap (e24-rft checkpoint-3250)

**Date:** 2026-08-27 · **Eval:** frozen 96-sample pool (certified, uuid%50==0), centered
volumetric IoU vs `gt_meshes_v15` · **Model:** e24-rft `consolidated-checkpoint-3250`
(the exact dir the original 0.876 bestof4 eval ran on).

## TL;DR

| Policy | Mean centered IoU |
|---|---|
| (c) greedy: draw 0 only, no repair | **0.7871** |
| (a) deployed: first-executing of 4 draws + repair | **0.8756** |
| (b) oracle: best-IoU draw of the 4 | **0.9222** |

**Oracle − deployed = +0.0466, paired bootstrap 95% CI [+0.031, +0.064].**
That is the ceiling for a critic reranker: it would cut the remaining error
(1 − 0.876 = 0.124) by **37%** if perfect. **Recommendation: GO (qualified)** — see below.

## Method (why this is a rerun, and why it's trustworthy)

The original `bestofn_eval.py` run cannot be re-scored: it early-stops (draws 1–3 were
never *generated* for the 85 samples solved at draw 0), keeps STLs in a deleted temp dir,
and strips candidate code from its JSON. So we reran with a patched all-draws eval
(`bo4_oracle_eval.py`): every sample gets all 4 draws (draw 0 greedy, 1–3 at T=0.7/top-p
0.95), each executed and scored independently; one greedy repair round only when all 4
fail (mirroring the deployed policy). All three policies are then computed on the **same
draws** — a paired comparison, tighter than any cross-run one.

Run environment: campus cluster was off-limits for compute (production only), so the run
executed on wpk-serv-05 + wpk-serv-06 — 16 single-H200 workers (8 per node, `stride 16`,
6 samples each), ~19 min wall. Env pinned to the cluster `.venv` (torch 2.13.0+cu130,
transformers 5.15.1, HF `generate` — same code path as the original eval; no vLLM).

**Parity validation against the original run** (per-sample records pulled from the cluster):

- Rerun deployed mean 0.8756 vs original 0.8765 (Δ = −0.0009).
- Median per-sample |deployed diff| = 0.000; winning-draw (`by_k`) identical on 89/96.
- 51/85 greedy draws reproduce the original IoU **bit-exactly** across L40S→H200
  (the rest shift via batch-composition/hardware numerics; sampled draws differ by design).
- Per-draw exec rates 84–90/96 (draw 0: 84, draw 1: 90, draw 2: 87, draw 3: 86);
  70/96 samples had all 4 draws execute. Coverage by deployed draw {0: 84, 1: 10, 2: 1,
  none: 1} ≈ original {0: 85, 1: 8, 2: 2, none: 1}.

## The gap, dissected

| Gap (paired, same draws) | Mean | Bootstrap 95% CI |
|---|---|---|
| oracle − deployed (critic ceiling) | **+0.0466** | [+0.0311, +0.0639] |
| oracle − greedy | +0.1351 | [+0.0832, +0.1946] |
| deployed − greedy (value of best-of-4 exec-gating) | +0.0885 | [+0.0394, +0.1459] |

Which draw is best vs which the deployed policy takes:

| | draw 0 | draw 1 | draw 2 | draw 3 | none |
|---|---|---|---|---|---|
| deployed picks | 84 | 10 | 1 | 0 | 1 |
| oracle picks | 33 | 29 | 16 | 17 | 1 |

- Execution success is NOT the bottleneck — sampled draws execute as often as greedy.
  The deployed policy takes draw 0 for 84/96 samples, but draw 0 is the *best* draw for
  only 33/96. Selection, not coverage, is what best-of-4 currently wastes.
- 50/96 samples have a strictly better draw than the deployed pick; 25 gain >0.05,
  18 gain >0.10.
- **The gap is concentrated: the 18 samples with gap >0.10 carry 79% of the total gap
  mass (91% from the 25 with gap >0.05).** A critic does not need fine ranking near the
  top — it needs to catch gross mistakes (mis-scaled/mis-shaped parts that still
  execute, e.g. deployed IoUs of 0.00/0.17/0.36 where a sibling draw had 0.05–0.63).

## Go / no-go vs the ±0.03–0.05 seed-noise bar

The +0.047 mean gap sits at the top of the noise band, but the bar applies to *unpaired
cross-run* comparisons; this measurement is paired on identical draws and its CI
[+0.031, +0.064] excludes zero decisively. (Empirically, the deployed mean reproduced
across cluster→lab reruns to ±0.001.) The ceiling is real, not noise.

**GO, qualified:** a critic reranker is worth a spike, with expectations set by the
structure above — a *perfect* critic gains +0.047 (0.876→0.922); a realistic one that
only catches the large-gap failures could still capture ~0.03–0.04 of it, because 79%
of the gap lives in 18 obviously-wrong picks. The cheapest version worth testing first:
a geometry-side sanity scorer (bbox/volume consistency vs the drawing's dimension text)
rather than a learned critic, since the wins are gross-error cases, not fine ranking.
Caveats: (i) a learned critic that ranks near-ties adds little (46/96 samples have
gap ≤0.001); (ii) gains stack on top of best-of-4's existing +0.089 over greedy, so
sampling more draws (k>4) plus the same critic may widen the ceiling further — the
per-draw exec rates (~90%) say candidates are cheap.

## Artifacts

- `bo4_oracle_summary.json` (committed) — per-sample per-draw exec/IoU + policy picks.
- `artifacts/shards/bo4_oracle_w*.json` (gitignored; also on serv-05/06 under
  `/srv/scratch/bimrose2/drawing_agent_exp1/out_bo4_oracle/`) — full records incl.
  candidate code; candidate .py/.stl under `.../out_bo4_oracle/candidates/`.
- `artifacts/original_bestof4-checkpoint-3250.json` — original run's per-sample records
  (cross-check source).
- Per-sample table: appendix below.

## Appendix — per-sample table

(draw IoUs; `--` = did not execute; sorted by oracle−deployed gap)

| key | d0 | d1 | d2 | d3 | deployed (by) | oracle (draw) | gap |
|---|---|---|---|---|---|---|---|
| 08734382-459 | 0.166 | 0.631 | 0.205 | 0.200 | 0.166 (0) | 0.631 (1) | +0.465 |
| 00199e66-2f8 | 0.683 | 1.000 | 1.000 | 1.000 | 0.683 (0) | 1.000 (1) | +0.317 |
| 058f2c3a-cfc | 0.739 | 0.998 | 0.851 | -- | 0.739 (0) | 0.998 (1) | +0.258 |
| 087bbb7a-c87 | 0.787 | 0.996 | 0.964 | 0.717 | 0.787 (0) | 0.996 (1) | +0.209 |
| 0fdd267e-0ea | -- | 0.791 | 0.877 | 1.000 | 0.791 (1) | 1.000 (3) | +0.209 |
| 05d7977c-c02 | -- | 0.793 | 1.000 | 1.000 | 0.793 (1) | 1.000 (3) | +0.207 |
| 02b4260a-2c8 | 0.798 | 0.815 | 0.708 | 1.000 | 0.798 (0) | 1.000 (3) | +0.202 |
| 0f48f6f2-1b8 | 0.815 | 0.562 | 0.806 | 0.995 | 0.815 (0) | 0.995 (3) | +0.180 |
| 04a4e152-726 | 0.662 | 0.807 | 0.842 | 0.791 | 0.662 (0) | 0.842 (2) | +0.180 |
| 0b144460-77a | 0.820 | 0.619 | 1.000 | 0.717 | 0.820 (0) | 1.000 (2) | +0.180 |
| 080b2e00-c9b | 0.808 | 0.965 | 0.861 | 0.834 | 0.808 (0) | 0.965 (1) | +0.157 |
| 0ce4f582-33c | 0.816 | 0.857 | 0.853 | 0.968 | 0.816 (0) | 0.968 (3) | +0.152 |
| 0f65741c-449 | 0.810 | 0.959 | 0.806 | 0.794 | 0.810 (0) | 0.959 (1) | +0.149 |
| 0b611efc-c10 | 0.631 | 0.780 | 0.747 | 0.747 | 0.631 (0) | 0.780 (1) | +0.149 |
| 0d2a56a4-4a6 | 0.805 | 0.838 | 0.932 | 0.945 | 0.805 (0) | 0.945 (3) | +0.140 |
| 0a7b7956-680 | 0.836 | 0.784 | 0.971 | 0.729 | 0.836 (0) | 0.971 (2) | +0.135 |
| 0a559fe2-ac3 | 0.701 | 0.833 | 0.587 | 0.808 | 0.701 (0) | 0.833 (1) | +0.133 |
| 03dfa680-4b6 | 0.839 | 0.781 | 0.658 | 0.959 | 0.839 (0) | 0.959 (3) | +0.120 |
| 024cdfc2-289 | 0.870 | 0.957 | 0.962 | 0.874 | 0.870 (0) | 0.962 (2) | +0.092 |
| 0d4e9816-812 | 0.910 | 0.985 | 0.910 | 0.904 | 0.910 (0) | 0.985 (1) | +0.075 |
| 0cd10c0c-4f2 | 0.893 | 0.966 | 0.893 | 0.893 | 0.893 (0) | 0.966 (1) | +0.073 |
| 07035802-864 | 0.929 | 1.000 | 0.857 | 1.000 | 0.929 (0) | 1.000 (1) | +0.071 |
| 0730e4f2-e95 | 0.930 | 1.000 | 0.987 | 0.946 | 0.930 (0) | 1.000 (1) | +0.070 |
| 0e14533a-a75 | 0.912 | 0.980 | 0.000 | 0.980 | 0.912 (0) | 0.980 (1) | +0.068 |
| 028bb3be-e82 | 0.927 | 0.990 | 0.994 | -- | 0.927 (0) | 0.994 (2) | +0.067 |
| 02c2c534-fdf | -- | 0.000 | -- | 0.048 | 0.000 (1) | 0.048 (3) | +0.048 |
| 061ae590-e22 | 0.953 | 0.555 | 0.953 | 1.000 | 0.953 (0) | 1.000 (3) | +0.047 |
| 0dd6ca4c-ec3 | 0.928 | 0.964 | 0.958 | -- | 0.928 (0) | 0.964 (1) | +0.035 |
| 0d9544aa-488 | 0.965 | 1.000 | 1.000 | 1.000 | 0.965 (0) | 1.000 (1) | +0.035 |
| 0120e88c-df7 | 0.959 | 0.988 | 0.984 | 0.994 | 0.959 (0) | 0.994 (3) | +0.035 |
| 0a8774b8-ccb | 0.968 | 0.981 | 1.000 | 1.000 | 0.968 (0) | 1.000 (3) | +0.032 |
| 042c25e6-40b | 0.958 | 0.958 | 0.986 | 0.958 | 0.958 (0) | 0.986 (2) | +0.028 |
| 0d838d1e-2f5 | 0.966 | -- | 0.981 | 0.990 | 0.966 (0) | 0.990 (3) | +0.024 |
| 053ba312-304 | 0.947 | 0.890 | 0.962 | 0.938 | 0.947 (0) | 0.962 (2) | +0.015 |
| 07832ef6-5dd | 0.986 | 0.988 | 0.963 | 1.000 | 0.986 (0) | 1.000 (3) | +0.014 |
| 09a06a3c-9e5 | 0.698 | 0.712 | -- | 0.658 | 0.698 (0) | 0.712 (1) | +0.014 |
| 103a4b9c-3e8 | 0.941 | 0.941 | 0.954 | -- | 0.941 (0) | 0.954 (2) | +0.013 |
| 01854fac-2b6 | 0.988 | 0.986 | 1.000 | 0.912 | 0.988 (0) | 1.000 (2) | +0.012 |
| 06e3334c-5c6 | 0.359 | 0.369 | 0.369 | 0.369 | 0.359 (0) | 0.369 (3) | +0.010 |
| 07d2049a-e04 | 0.985 | 0.960 | 0.989 | 0.993 | 0.985 (0) | 0.993 (3) | +0.008 |
| 07bfb06a-623 | 0.978 | 0.985 | 0.916 | 0.968 | 0.978 (0) | 0.985 (1) | +0.007 |
| 0f58d446-836 | 0.951 | 0.950 | 0.942 | 0.957 | 0.951 (0) | 0.957 (3) | +0.007 |
| 03fe9cac-607 | 0.954 | 0.583 | 0.960 | 0.938 | 0.954 (0) | 0.960 (2) | +0.006 |
| 0a3681ac-2be | 0.504 | 0.493 | 0.509 | 0.507 | 0.504 (0) | 0.509 (2) | +0.006 |
| 0979b252-eee | 0.993 | -- | 0.997 | 0.996 | 0.993 (0) | 0.997 (2) | +0.004 |
| 0264f04e-987 | -- | 0.979 | -- | 0.983 | 0.979 (1) | 0.983 (3) | +0.004 |
| 092593f2-bbb | 0.927 | 0.932 | 0.925 | 0.922 | 0.927 (0) | 0.932 (1) | +0.004 |
| 03b5b65e-5bd | 0.987 | 0.858 | 0.989 | 0.969 | 0.987 (0) | 0.989 (2) | +0.003 |
| 02042bd8-55d | 0.998 | 1.000 | 0.997 | 0.994 | 0.998 (0) | 1.000 (1) | +0.002 |
| 038de502-dae | 0.998 | 1.000 | 1.000 | 0.942 | 0.998 (0) | 1.000 (1) | +0.002 |
| 09ca4d7a-4a0 | 1.000 | 1.000 | 1.000 | 0.904 | 1.000 (0) | 1.000 (2) | +0.000 |
| 0cfc10be-e86 | 0.969 | 0.831 | 0.970 | 0.729 | 0.969 (0) | 0.970 (2) | +0.000 |
| 000bc5ac-ffb | 0.982 | 0.982 | 0.982 | 0.950 | 0.982 (0) | 0.982 (1) | +0.000 |
| 0e134a30-6df | 1.000 | 1.000 | 1.000 | 0.999 | 1.000 (0) | 1.000 (1) | +0.000 |
| 0975cab6-f02 | 0.992 | 0.992 | 0.992 | 0.992 | 0.992 (0) | 0.992 (1) | +0.000 |
| 067e685e-8e0 | 1.000 | 0.999 | 1.000 | 0.998 | 1.000 (0) | 1.000 (0) | +0.000 |
| 0cb7362e-599 | -- | 1.000 | 0.970 | 1.000 | 1.000 (1) | 1.000 (1) | +0.000 |
| 0ee24452-202 | 0.971 | 0.971 | 0.922 | 0.886 | 0.971 (0) | 0.971 (0) | +0.000 |
| 06b4e884-848 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 |
| 0eec11b2-ced | -- | 0.988 | 0.957 | -- | 0.988 (1) | 0.988 (1) | +0.000 |
| 0024c6d8-aa7 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 |
| 00874eac-be8 | -- | 1.000 | 0.935 | -- | 1.000 (1) | 1.000 (1) | +0.000 |
| 00d1e3d6-db1 | 0.999 | 0.999 | 0.997 | 0.997 | 0.999 (0) | 0.999 (0) | +0.000 |
| 09dc90de-9ef | -- | 0.385 | -- | 0.355 | 0.385 (1) | 0.385 (1) | +0.000 |
| 0cfca2a4-82f | 0.959 | 0.949 | 0.959 | 0.959 | 0.959 (0) | 0.959 (0) | +0.000 |
| 0a01a8f6-a78 | 1.000 | 0.949 | 0.961 | 0.961 | 1.000 (0) | 1.000 (0) | +0.000 |
| 014e0c04-50a | 1.000 | 0.993 | 0.992 | 0.975 | 1.000 (0) | 1.000 (0) | +0.000 |
| 0a0a5992-bf7 | 0.902 | 0.759 | 0.636 | 0.723 | 0.902 (0) | 0.902 (0) | +0.000 |
| 0feed9be-4eb | 1.000 | -- | 0.997 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 |
| 04e8b530-888 | -- | 0.831 | 0.807 | -- | 0.831 (1) | 0.831 (1) | +0.000 |
| 0d6ee184-71d | 0.977 | 0.977 | 0.947 | 0.933 | 0.977 (0) | 0.977 (0) | +0.000 |
| 1027d3e0-b91 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 |
| 01bcfa42-0f4 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 |
| 04e95c60-20c | 0.928 | 0.919 | 0.918 | 0.878 | 0.928 (0) | 0.928 (0) | +0.000 |
| 0d8231a8-81f | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 |
| 01f125ec-6a2 | 0.919 | 0.859 | 0.866 | 0.857 | 0.919 (0) | 0.919 (0) | +0.000 |
| 082d1e48-208 | 1.000 | 1.000 | 0.982 | 0.981 | 1.000 (0) | 1.000 (0) | +0.000 |
| 104587fa-61e | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 |
| 0580ef4e-eda | 0.416 | 0.412 | 0.390 | 0.416 | 0.416 (0) | 0.416 (0) | +0.000 |
| 082dbea2-e3f | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 (0) | 1.000 (0) | +0.000 |
| 10827958-85b | 0.778 | 0.587 | 0.616 | 0.605 | 0.778 (0) | 0.778 (0) | +0.000 |
| 02133c18-027 | 0.894 | 0.894 | -- | 0.894 | 0.894 (0) | 0.894 (0) | +0.000 |
| 0ae0be88-1a8 | 1.000 | 0.999 | 1.000 | 0.942 | 1.000 (0) | 1.000 (0) | +0.000 |
| 108abe88-f9f | 0.959 | 0.956 | -- | 0.933 | 0.959 (0) | 0.959 (0) | +0.000 |
| 10a652e2-346 | 1.000 | 0.496 | -- | 0.541 | 1.000 (0) | 1.000 (0) | +0.000 |
| 05ede2e8-984 | 0.983 | 0.978 | -- | 0.977 | 0.983 (0) | 0.983 (0) | +0.000 |
| 08ceb60e-09e | 1.000 | -- | 1.000 | 0.998 | 1.000 (0) | 1.000 (0) | +0.000 |
| 10d0ca90-0d1 | 0.994 | 0.994 | 0.994 | 0.994 | 0.994 (0) | 0.994 (0) | +0.000 |
| 05f14712-467 | -- | -- | -- | -- | 0.000 (None) | 0.000 (None) | +0.000 |
| 090d59fe-be2 | -- | 0.741 | 0.535 | 0.355 | 0.741 (1) | 0.741 (1) | +0.000 |
| 0b9e23e2-2da | -- | -- | 0.987 | -- | 0.987 (2) | 0.987 (2) | +0.000 |
| 0e6d9ff8-bd0 | 0.961 | 0.354 | 0.781 | 0.770 | 0.961 (0) | 0.961 (0) | +0.000 |
| 10d37114-259 | 1.000 | 1.000 | 1.000 | -- | 1.000 (0) | 1.000 (0) | +0.000 |
| 0c43354e-b72 | 1.000 | 0.997 | 1.000 | 0.997 | 1.000 (0) | 1.000 (0) | +0.000 |
| 0ead60ac-739 | 1.000 | 1.000 | 1.000 | 0.823 | 1.000 (0) | 1.000 (0) | +0.000 |
| 10dff308-8a8 | 1.000 | 0.994 | 0.584 | 0.953 | 1.000 (0) | 1.000 (0) | +0.000 |
