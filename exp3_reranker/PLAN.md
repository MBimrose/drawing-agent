# Exp 3 — Best-of-N selection policies (closing the oracle gap offline)

**Question:** exp1 measured a +0.047 oracle−deployed gap (0.876 → 0.922) for best-of-4,
concentrated in 18 gross-error samples (gap >0.10 → 79% of gap mass); draw 0 is best for
only 33/96. Can a *selection policy* — heuristics and/or a VLM critic, no new champion
inference — capture a CI-significant chunk of that gap?

**Data (all offline, from exp1):** `exp1_bestof4_oracle/artifacts/shards/bo4_oracle_w*.json`
— 96 samples × 4 draws, each with candidate code, exec status, centered IoU (verified:
384 draws, 384 with code, 347 exec_ok). Drawing PNGs in
`/srv/scratch/bimrose2/drawing_agent_exp1/wds_dataset/eval_cache_v15.pkl` (`samples[key]["png"]`;
GT code/trace in the same cache is NEVER read at selection time). GT meshes/IoU are used
for *evaluation only* — selection sees only candidate code, re-executed candidate meshes,
and the drawing.

**Ground rules**
- Selection-time inputs: candidate code, re-executed candidate geometry, the drawing PNG.
  No GT meshes, no GT code, no shard IoUs.
- Policies choose among draws that executed *in the shards* (exec_ok); if none execute,
  fall back to the deployed repair path (identical for all policies — 1 sample).
- Evaluation: policy pick → that draw's shard IoU. Paired per-sample deltas vs deployed,
  20k-resample paired bootstrap 95% CI (same machinery as exp1's `analyze_bo4.py`).
  A policy WINS only if its CI vs deployed excludes zero.
- Heavy files (STL/STEP/renders) under `/srv/scratch/bimrose2/drawing_agent_exp3/` and
  `exp3_reranker/artifacts/` (gitignored). Committed: code, PLAN, RESULTS, compact JSONs.

## Steps

1. **Data prep** — `load_data.py`: merge shards → `merged_bo4.json` view; sanity-count
   96×4; recompute deployed/oracle/greedy means and match exp1's RESULTS numbers exactly.
2. **Re-execution + features** — `rexec_features.py`: re-execute all 384 candidate
   scripts CPU-parallel (exp1 env python, temp dirs outside repo), tessellate, measure:
   volume, sorted bbox extents, aspect ratios, watertight, n_mesh_components, n_solids,
   n_faces/planar/cylindrical (STEP via build123d). Persist `features.json` (compact,
   committed). Cross-check exec_ok agreement vs shards + vs exp1's persisted STLs
   (workers 0–7 live on this box) — flag any nondeterminism.
3. **Drawing view features** — `drawing_views.py`: the drawings use blue ink for
   dimensions/labels and dark ink for part geometry. Filter to low-saturation dark pixels,
   connected-component cluster, assign Top/Front/Right/ISO by layout (front bottom-left,
   top above it, right beside it, ISO far right), emit per-view ink-bbox aspect ratios →
   `drawing_views.json`. Validate visually on a handful of drawings; report extraction
   success rate. (Scale-invariant ratios only; title block/ISO excluded.)
4. **Heuristic policies** — `policies.py`:
   - Baselines: deployed (first-exec), oracle, greedy, random-exec (analytic expectation).
   - Degenerate filter: tiny/zero volume, extreme aspect, non-watertight, many components.
   - Consensus: pairwise distance on (log-volume, sorted extents) among executing draws;
     outlier flag + medoid ranking. n_exec=2 ties treated conservatively.
   - Drawing-aspect consistency: candidate bbox ratios vs extracted view ratios.
   - Combined gate: first-exec unless flagged gross error → next-best-by-consensus.
   - Full ablation grid of the components.
5. **VLM critic** — `render_candidates.py` (3-view orthographic line renders per
   executing candidate, reusing exp2's `inspect_candidate.py` conventions,
   /software/python-3.11.1 has build123d+cairosvg) + `vlm_critic.py`: Kimi K3 via hub
   router (verified image-capable in exp2). One call per sample: drawing + shuffled
   labeled candidate renders → JSON {per-candidate 0–10 scores, best, gross_error flags}.
   Policies: vlm-pick, vlm-score-argmax(tie→first-exec), vlm-gate(first-exec unless VLM
   flags it), hybrid (heuristic gate → VLM adjudicates only flagged samples, ~cheap).
   Persist raw verdicts to artifacts/ for reproducibility.
6. **Probe** — `probe_critic_model.py`: 2–3 calls to `claude-qwen36-27b-build123d-critic`
   to learn its expected input format; include as a policy only if usable as-is.
7. **Evaluation** — `evaluate.py`: policy table (mean IoU, Δ vs deployed, paired 95% CI,
   % of oracle gap captured, fixes among the 18 gross-error samples, breaks elsewhere,
   cost in model calls + wall-clock). → `policy_results.json` + RESULTS.md.

## Progress log

- 2026-08-27: dir created; shards verified (96×4, 347 exec_ok, per-draw code+IoU present).
  Eval-cache PNGs confirmed (blue dims / dark geometry). Envs checked: exp1 env python
  (b123d 0.11.1, trimesh 5.0) for exec+measure; /software/python-3.11.1 for renders
  (cairosvg). 128 CPUs available.
- 2026-08-28: `bo4data.py` reproduces exp1 exactly (0.8756/0.9222/0.7871, 18 gross).
  Re-exec of all 384 candidates: 36 s at 64 workers, **384/384 exec_ok agreement** with
  shards, volumes match exp1's persisted STLs to ≤1e-6 rel. New baseline measured:
  random-exec-expectation 0.8697 (< deployed — first-exec already beats random).
- Drawing-view extraction: blue-ink filter + alignment-based view assignment
  (front/right share y-span, front/top share x-span) → full front+top+right on 73/96;
  cross-view scale consistency within 3% on ~95% of those (self-validating).
- Heuristic findings: degenerate-solid checks are a DEAD END on this champion —
  execution already filters junk; bad candidates are watertight single solids that are
  mis-scaled/mis-shaped (not_watertight/many_solids fire mostly on GOOD candidates,
  median IoU 0.86/0.98 → gating on them LOSES −0.009). Consensus medoid-always +0.013,
  aspect-best-always +0.017 (both CI-significant). **Combined score
  (consensus med-dist + aspect mismatch, switch only if it beats first-exec by >0.05
  margin): +0.0222 [CI +0.009, +0.038], 13 switches ALL positive, 8/18 gross fixed,
  0 breaks.** All 3-view renders done (347/347, 47 s).
- Probe `claude-qwen36-27b-build123d-critic`: listed by router /v1/models but backend
  404s ("model does not exist") — its qwen3.6 server (wpk-serv-06:8000) is stopped.
  Not usable as-is → excluded per plan. (2 probe calls, both fail; router itself fine.)
- Kimi K3 critic harness written (1 call/sample, drawing + ≤4 labeled renders in
  key-seeded shuffled order, thinking-aware max_tokens 6000, JSON verdict
  scores/best/gross). Smoke 3/3 parsed; 90–343 s/call, 10–18k output tokens (thinking).
- Shape-space consensus added (`pairwise_iou.py`, 549 candidate-pair mesh IoUs in 25 s,
  GT-free): alone +0.014 (beats bbox-consensus alone +0.009), but bbox+aspect combined
  stays the best no-model policy (+0.0222); triple-stacking adds breaks, not gains.
  Root cause identified: ALL 10 unfixed gross-error samples have identical bboxes
  across draws and majority-shared wrong shape — consensus (of any kind) cannot see
  a minority-correct draw; needs the drawing (aspect can't see internal features).
- **Ops lessons (full Kimi run):** (i) harness background tasks were killed ~23 min in
  — run long jobs via `setsid nohup … &` detached, with per-sample checkpoint
  (`vlm_kimi.jsonl`) + `--resume` (now implemented); (ii) the hub Kimi backend degrades
  badly above ~3–4 concurrent vision calls (10 workers → 900 s timeouts + retry churn,
  1 sample/37 min; the one that landed took 57 s of service time). Restarted detached
  at 4 workers, 01:30.
- `claude-qwen36-27b-build123d-critic` probe: router lists it, backend 404s (qwen3.6
  server on serv-06:8000 stopped) — not usable as-is, excluded.
- 2026-08-28 (final): full Kimi run done — 93/96 verdicts, 91 calls, 0.76M/1.25M
  tokens, ~110 min at 4-way. **vlm-pick +0.0133 [−0.005, +0.031] NOT significant**
  (11/18 gross fixed but 12 breaks, worst −0.416 off a perfect d0); hybrids
  significant (+0.0165/+0.0174) but below the pure heuristic. Final verdict:
  **deploy the no-model combined heuristic (+0.0222 [+0.009, +0.038], 48% of gap,
  0 regressions); skip the VLM critic.** RESULTS.md written; all committed.
