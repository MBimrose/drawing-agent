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

**Once `ssh cc-login` works:**
1. Verify remote layout: `runs/e24-rft/checkpoint-3250` kind (hf vs dcp+consolidated),
   `eval_cache_v15.pkl`, `gt_meshes_v15/`, `.venv`, and locate the original bestofn out
   JSON (per-sample deployed records, for cross-checking our rerun against 0.876).
2. `mkdir -p /projects/.../drawing_agent_exp1/logs`, scp `bo4_oracle_eval.py` +
   `exp1_bo4_oracle.sbatch` up, `sbatch` it, poll `squeue`/log tail.
3. Pull `out_bo4_oracle/bo4_oracle.json` back into `artifacts/` (gitignored), run
   `analyze_bo4.py`, write RESULTS.md (three means, per-sample table, histogram,
   go/no-go vs the ±0.03–0.05 bar), commit.
