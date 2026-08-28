# Exp 1 — Best-of-4 oracle gap

**Question:** on the e24-rft ckpt-3250 best-of-4 eval, how much mean IoU separates
(a) the deployed policy (first draw that executes → 0.876 with repair),
(b) the oracle (best-IoU draw of the 4), and
(c) greedy draw 0 only?
The (b)−(a) gap is the ceiling for a critic reranker; if it's under the ±0.03–0.05 noise bar,
the critic path is not worth building.

**Where the data is:** campus cluster, `/projects/illinois/eng/ece/wpk/bimrose2/drawing_vlm`
(runs/, gt_meshes_v15, eval pool). Cluster access is Duo-gated — prep everything locally first,
poll `ssh -o BatchMode=yes cc-login true` until the user opens the ControlMaster.

**Plan:**
1. Read `vendor/drawing-vlm/train_v14/geom/bestofn_eval.py`: determine exactly what per-draw
   state a best-of-4 run persists (scripts? STEPs? per-draw IoU?). Decide: pure re-score of
   existing state (CPU-only, preferred) vs a patched all-draw-scoring rerun (GPU sbatch).
2. Write the analysis script(s) here, self-contained, importing geom/iou + exec_harness.
3. When ssh works: locate the run state on the cluster, run the analysis there (or pull the
   needed candidate scripts + GT STLs locally and score in mcp_env), never modifying existing
   runs/ state — write to a fresh output dir.
4. RESULTS.md: the three means, per-sample table, draws histogram (which draw wins how often),
   and a go/no-go recommendation for critic reranking (compare gap vs noise bar).

**Rules:** read-only against drawing-vlm's repo and run dirs. If a GPU rerun is unavoidable,
copy their sbatch conventions (account/partition) from `train_v14/sbatch/`, submit under this
project's own output dir, and poll for completion.

---

## Status 2026-08-27 (prep complete, blocked on Duo)

**Step-1 finding: a pure re-score of existing state is IMPOSSIBLE — GPU rerun required.**
`bestofn_eval.py` (a) works in a `tempfile.TemporaryDirectory` (STLs deleted at exit),
(b) pops `last_reply`/`last_rec` from records before writing JSON (no candidate code
persisted), and (c) **early-stops**: `todo = [i for r if not exec_ok]` — draws 1–3 were
never *generated* for the 85/96 samples solved at draw 0. The oracle's candidates don't
exist anywhere. Bonus finding from the vendored metrics snapshot
(`results/e24-rft.bestof4-checkpoint-3250.json`): coverage {0: 85, 1: 8, 2: 2, None: 1} —
draw 3 never rescued a sample and the repair round never fixed the 1 unsolved one.

The rerun is *better* anyway: all three policies computed on the SAME 4 draws per sample
= a paired comparison (bootstrap CI on per-sample gaps), tighter than cross-run seed noise.

**Prep written (this dir):**
- `bo4_oracle_eval.py` — patched best-of-4: all k draws for every sample (no early stop),
  each executed + IoU-scored independently, per-draw code persisted inline in the output
  JSON + as .py/.stl under `<out>/candidates/`; one greedy repair round only when all 4
  fail (mirrors deployed policy); refuses DCP consolidation into runs/ (read-only rule);
  incremental JSON dumps per draw. Imports the cluster repo's geom modules read-only
  (`DRAWING_VLM_TRAIN` env overridable).
- `analyze_bo4.py` — CPU/stdlib-only: three means, paired gaps with 20k-resample
  bootstrap 95% CIs, deployed-vs-oracle draw histograms, per-sample markdown table
  (`--md` writes a RESULTS.md draft). Tested on synthetic data.
- `exp1_bo4_oracle.sbatch` — account/partition/gres copied from their `geom_eval.sbatch`
  (wpk/wpk, ccc0442, 4×L40S, 500G); one-shot, 24h cap, logs + outputs under
  `/projects/illinois/eng/ece/wpk/bimrose2/drawing_agent_exp1/` (fresh dir, ours).

**Once `ssh cc-login` works:** (superseded — see pivot below)

## Pivot 2026-08-27: cluster compute barred → run on serv-05 + serv-06

Duo opened and slurm job 10195292 was submitted to ccc0442, but the user then directed
that NO compute run on the campus cluster (production jobs only) and cancelled the job
(`scancel 10195292`). Cluster is now a data source only.

What happened instead:
- Raw `checkpoint-3250` was rotated away on the cluster; the surviving
  `runs/e24-rft/geom_eval/consolidated-checkpoint-3250` is the exact dir the original
  bestof4 eval ran on (its JSON's `ckpt` field confirms). Pulled it (51G, byte-size
  verified) plus `eval_cache_v15.pkl`, `gt_meshes_v15/` (2103 STLs), base-model
  processor/tokenizer configs, and the original per-sample bestof4 records
  (→ `artifacts/original_bestof4-checkpoint-3250.json`) to
  `/srv/scratch/bimrose2/drawing_agent_exp1/` on wpk-serv-06.
- Self-contained tree there: copied `train_v14/` code + pinned uv venv mirroring the
  cluster `.venv` (torch 2.13.0+cu130, transformers 5.15.1, accelerate 1.14.0,
  torchvision 0.28.0, numpy 2.5.2, trimesh 5.0.0, build123d 0.11.1, manifold3d,
  qwen-vl-utils, webdataset 1.0.2) — keeps HF `generate` parity with the original run.
- `bo4_oracle_eval.py` gained `--worker/--stride` (shards `keys[worker::stride]`) and
  `--model-base` (points cfg model_id at the local processor copy; vendor code untouched).
- `run_node.sh`: 8 single-GPU workers per node (54GB bf16 fits one H200).
  serv-06 = workers 0–7, serv-05 = workers 8–15, stride 16 (6 samples each).
  Tree rsynced to serv-05 at the same path. Per-worker JSONs merged by `analyze_bo4.py`.

## Done 2026-08-27 (same day)

Smoke test reproduced the original run's first-sample greedy IoU bit-exactly
(0.982221348022466) across cluster L40S → lab H200. Full 16-worker run finished in
~19 min, 0 errors. Rerun deployed mean 0.8756 vs original 0.8765. **Final numbers:
greedy 0.7871 / deployed 0.8756 / oracle 0.9222; oracle−deployed +0.0466
[95% CI +0.031, +0.064]. Verdict: qualified GO for a critic reranker** — see RESULTS.md.
Per-sample data: `bo4_oracle_summary.json` (committed); full shards with candidate code
in `artifacts/shards/` and on both servers under
`/srv/scratch/bimrose2/drawing_agent_exp1/out_bo4_oracle/`.
