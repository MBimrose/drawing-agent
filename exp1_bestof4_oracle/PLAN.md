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
