# Exp 4 — Frontier model + agentic harness vs the cluster fine-tune

**Question:** does Kimi K3 (a frontier generalist) + the exp2 agentic harness compare to the
e24-rft fine-tuned 27B on the fine-tune's OWN frozen benchmark — the 96-sample certified
eval pool? Reference numbers (exp1, same 96 samples, same metric):

| e24-rft ckpt-3250 policy | mean centered IoU |
|---|---|
| greedy (draw 0 only) | 0.787 |
| deployed best-of-4 + repair | 0.876 |
| oracle-of-4 (critic ceiling) | 0.922 |

**Design:**
- **Data:** the SAME frozen pool exp1 scored: first 96 keys of
  `eval_cache_v15.pkl` `pools["certified"]` that have a GT mesh in `gt_meshes_v15/`
  (verified identical to exp1's `bo4_oracle_summary.json` key set). Drawings decoded from
  the cache (`_decode_png` semantics: RGBA composited over white) to
  `artifacts/drawings/<uuid>.png` (gitignored, regenerable via `harness/prep_data.py`).
  GT STLs referenced in place from
  `/srv/scratch/bimrose2/drawing_agent_exp1/wds_dataset/gt_meshes_v15/`.
- **Solver:** Kimi K3 via hub router (wpk-serv-07:3456, anthropic-messages) — image input
  verified in exp2. Concurrency 5 (exp3 shares the router).
- **Arms** (exp2 harness design, `harness/run_arms.py` adapted from exp2):
  - *single-shot*: turn-1 completion, executed, scored;
  - *agentic*: same turn-1 seeds a loop, budget 12 model calls, measurement-only feedback
    (exec/stderr, bbox/volume/face census + cylinder radii, one self-render per turn),
    NO ground truth, no PASS verdicts; final = last executing candidate (checkpoint-first).
  - Prompt = exp2's cadgenbench-informed system prompt with the view-conventions paragraph
    adapted to the v15 sheet style (unlabeled third-angle views: top above front, right side
    view beside front; possible SECTION views; ISO VIEW (NTS) pictorial; ⌀/↓/⌵ hole-callout
    symbols; C-chamfer notes). max_tokens 16000 (exp2 footnote: 8k truncated Kimi's
    thinking on some parts; 16k keeps "single-shot capability" measurable), T=0.6.
- **Scoring:** centered volumetric IoU (`harness/iou.py`, verbatim exp2 copy = verbatim
  adaptation of train_v14/geom/iou.py), same exec harness semantics as the champion eval
  (`harness/exec_harness.py`), executed under /software/python-3.11.1 (build123d 0.10),
  scripts run in temp dirs outside the repo.
- **Variance probe (if wall-clock allows):** independent second run (new turn 1 + loop) on a
  24-sample subset, tag `seed2`, to estimate loop variance.
- **Analysis:** per-sample table; means; STaR-gate yield (IoU≥0.8, Kimi-as-RFT-teacher
  relevance); paired per-sample comparison vs exp1's greedy/deployed/oracle records;
  difficulty buckets derived from champion performance (the eval metadata itself has no
  difficulty labels — samples are png/code/trace only); cost per part (model calls, tokens,
  wall-clock) vs champion's 4 draws honestly noted (Kimi = 1 attempt + loop, champion = 4
  independent draws + repair).

**Deliverables:** `results.json` + `results_seed2.json` (committed, top level),
trajectories under `trajectories/`, RESULTS.md with the headline verdict: where does
Kimi+loop land relative to 0.787 / 0.876 / 0.922, and what does that say about
harness-vs-fine-tuning on this task?

---

## Progress log (2026-08-28)

- Pool verified: 96 keys == exp1 benchmark key set; drawings 1920×1280 RGB.
- Harness modules copied verbatim from exp2 (exec_harness, iou, inspect_candidate);
  run_arms adapted (manifest from prep_data, v15 prompt paragraph, usage accounting).
- Smoke (2 parts): harness OK end-to-end. 00199e66 ss=ag=0.976 (champ greedy 0.683,
  oracle 1.000); 000bc5ac ss=ag=0.453 — Kimi read the cap's pocket as 2 mm deep
  instead of a 2 mm wall (6 mm pocket) and FINAL'd: the exp2 "confident misread"
  failure mode, on the champion's home turf. Champ deployed 0.982 there.
- Full 96-part run launched (5 workers, resume-safe incremental results.json).
- Main pass done (~7 h wall; router shared with exp3 → 15 transient 502s, retried in a
  second pass). Wave of runaway-thinking turns (~100k chars, truncated, no code) exposed a
  harness bug inherited from exp2: `is_final` matched the word FINAL anywhere in the reply,
  so 7 runaway turn-1s were misread as termination (ss=0, ag=0, loop never ran). Fixed
  (FINAL must sit in the last 300 chars of a <2000-char reply — genuine FINALs observed
  ≤1.3k chars, runaways ~100k) and those 7 + remaining errors redone with the fixed code.
  exp2's numbers are unaffected (its FINAL replies were all genuine).
- 95/96 scored: kimi ss 0.555 / ag 0.732 vs champ greedy 0.794 / deployed 0.883 /
  oracle 0.925. Kimi ag exec 95/95. Notable: Kimi+loop solves the champion's only
  unsolved part (05f14712: 0.890 vs 0.000); max(kimi_ag, champ_dep) = 0.919 ≈ champ
  oracle ceiling; on 18 champ-hard parts Kimi passes the 0.8 STaR gate on 6.
- seed2 variance probe (24 parts, independent run) + last errored part in flight.
- **DONE 2026-08-28: 96/96 + seed2 24/24 scored, 0 errors. Final: kimi ss 0.549 /
  agentic 0.724 vs champ 0.787 greedy / 0.876 deployed / 0.922 oracle — fine-tune wins
  its home benchmark decisively; Kimi+loop beats deployed on the champ-hard bucket
  (0.612 vs 0.560), solves the champion's only unsolved part, and max(kimi, champ) =
  0.919 ≈ oracle ceiling. RESULTS.md has the full verdict; 45+15 accepted
  trajectories under trajectories/.**
