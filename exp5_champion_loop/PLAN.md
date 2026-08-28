# Exp 5 — Champion-in-the-loop (fine-tuning × agentic harness)

**Question:** put the fine-tuned champion itself (e24-rft `consolidated-checkpoint-3250`)
into the exp2-style measurement-feedback loop on the frozen 96-sample eval. Does the loop
add IoU ON TOP of what fine-tuning + best-of-4 + repair already deliver (deployed 0.876),
and how close does it get to (or past) the 0.922 oracle-of-4?

Exp2 showed the loop transforms the *base* qwen3.8-27b (0.128 → 0.728 on fresh parts) and
adds a small tail win for a strong teacher (Kimi +0.118). This experiment measures the
composition that actually matters for the product: champion + loop, on the frozen pool
where every other number lives.

**Foundation (verified, not rebuilt):**
- exp1 self-contained tree on BOTH nodes at `/srv/scratch/bimrose2/drawing_agent_exp1/`
  (champion weights 51G, pinned uv env torch 2.13.0+cu130 / transformers 5.15.1 /
  build123d 0.11.1 / manifold3d / qwen_vl_utils, `eval_cache_v15.pkl`, `gt_meshes_v15/`,
  base-model processor at `models/Qwen3.8-27B`, vendored `train_v14/` code). Both nodes
  idle (8×H200 each; checked 2026-08-27).
- exp1's `bo4_oracle_eval.py` + `run_node.sh`: worker/stride sharding, batched HF
  `generate`, chat-template kwargs, degenerate-output guard, incremental JSON dumps.
- exp2's `harness/run_arms.py` + `inspect_candidate.py`: the loop shape, measurement-only
  feedback templates (no GT, no PASS verdicts), render pruning, checkpoint-first final.
- `/software/python-3.11.1/bin/python3.11` exists on BOTH nodes with build123d 0.10 +
  cairosvg + trimesh → measurement/render subprocess interpreter (same as exp2).
- vendored `geom_eval_worker.build_repair_messages` / `feedback_text`: the EXACT repair
  message format the deployed eval uses — reused verbatim for exec-failure feedback so the
  failure-repair path matches what the champion has already demonstrated it handles.

**Loop arm (one arm; greedy throughout, fully deterministic):**
1. Turn 1 = greedy generation with the training system/user prompt = exp1's draw 0
   (the known 0.787 baseline). Parity-check a few samples against
   `exp1_bestof4_oracle/bo4_oracle_summary.json` d0 IoUs before the full run.
2. Up to **8 feedback rounds** per sample. Feedback is measurements ONLY:
   - exec failure → the vendored `feedback_text` (stderr tail, fix request) — deployed
     repair format;
   - exec success → bbox / volume / solid+face census / cylindrical radii of the
     candidate, plus (mode-dependent) a Top/Front/Right line-render of the candidate,
     and an invitation to either output a full corrected script or reply FINAL.
   No ground truth anywhere in the loop; no verdicts (cadgenbench PASS-tool trap).
3. Multi-image support (drawing + per-round self-render in later user turns) is tested
   EARLY on 2–3 samples. If the champion's chat template / behavior misbehaves with
   mid-conversation images, fall back to text-only measurements and say so in RESULTS.
   Only the newest render stays as an image; older ones become text stubs (exp2 policy).
4. Stop: model replies FINAL (no code) / emits code identical to its previous candidate
   (convergence — greedy decode would loop forever) / 2 consecutive no-code replies /
   budget. Final answer = LAST executing candidate (checkpoint-first). Best-seen is also
   recorded (out-of-loop, GT-scored) to price a keep-best policy.

**Scale-out:** 96 samples → 16 single-GPU workers (8/node, `keys[worker::stride]`,
stride 16), exactly exp1's pattern. Incremental JSON per worker per round.
Outputs under `/srv/scratch/bimrose2/drawing_agent_exp5/` on each node (exp1 tree is
read-only), summaries mirrored here.

**Analysis (paired per-sample, vs exp1's table):**
- loop-final vs greedy (same turn-1 → the loop delta is exact), bootstrap CI;
- loop-final vs deployed 0.876 and oracle 0.922 (per-sample from exp1's summary);
- rescues (exec-fail→working), refinements, regressions (final < turn-1), final-vs-best
  gap (does a keep-best policy pay?), rounds used, stop reasons;
- STaR angle: gate yield (IoU≥0.8) loop-final vs single greedy — loop as an rft_v3
  generator using the champion itself, no teacher;
- cost: wall-clock + GPU-hours vs the best-of-4 policy (~19 min × 16 H200 in exp1).

**Files:** `loop_eval.py` (worker), `exec_harness.py` (exp2's STEP-preserving variant),
`inspect_candidate.py` (exp2's, verbatim), `run_node.sh`, `analyze_loop.py`,
`loop_summary.json` + RESULTS.md at the end. Big artifacts stay in the run trees.

**Hygiene:** GPUs on both nodes released when done; no cluster contact; exp1 tree
read-only; run artifacts under `/srv/scratch/bimrose2/drawing_agent_exp5/`.

---

## Progress log

- 2026-08-27: dir created, infra verified (both nodes idle, exp1 trees present on both,
  sw-python with cairosvg on both). PLAN written.
- 2026-08-28 smoke 1 (exp1 worker-0's exact shard, 6 samples, renders on, greedy rounds):
  * **Turn-1 parity: bit-exact** on all 4 executing samples (0.982221/1.000/0.991644/
    0.970626 = exp1 d0 to 6 decimals); both exec failures match too.
  * **Multi-image works mechanically**: chat template + processor accept a render PNG in
    a mid-conversation user turn, batch generation fine, replies coherent. Renders clean.
  * Model understands FINAL: all 4 executing samples compared measurements+render and
    replied FINAL in round 1 (all are 0.97+ — reasonable).
  * **Pure greedy loops are degenerate**: both exec-failure samples regenerated
    byte-identical broken code from the stderr feedback (diff r0 r1 = identical).
    Consistent with exp1 (deployed repair almost never rescues; temperature draws do).
  * Decision: rounds ≥1 sample at **T=0.7/top-p 0.95** — exactly the deployed best-of-4
    draw settings, so loop rounds and bo4 draws spend the same kind of compute. Turn 1
    stays greedy (paired baseline intact). `--loop-temperature` added.
- Smoke 2 (8 hand-picked samples: 6 mediocre-greedy 0.17–0.63 + the 2 exec failures,
  max-rounds 4, T=0.7 rounds, renders on; 165 s after load):
  * **All 6 executing samples replied FINAL after ONE feedback round** — even at IoU
    0.166. The champion re-asserts its own reading (think-tails re-verify its beliefs,
    not the drawing) and stops. The soft "if a revision would help…" invitation is a
    free exit for an RFT-trained single-shot model.
  * T=0.7 repair DOES rescue what greedy cannot: 0cb7362e 0 → 0.970 (2 rounds);
    02c2c534 exec-rescued but geometry 0.0 (= its exp1 deployed outcome), then converged.
  * greedy 0.324 → final 0.445 on this set, entirely from the one rescue.
  * Change for smoke 3: FEEDBACK_OK rewritten as a re-derivation checklist (re-read
    every dimension from scratch, per-axis chain arithmetic for the TARGET, compare
    against measured bbox / hole radii / face counts, outline-vs-outline render compare)
    — still measurements-only, no verdicts. FINAL only if every check passes.
- Smoke 3 (same 8 keys, checklist feedback, 172 s): the checklist closes the soft FINAL
  exit (5 of the 6 mediocre parts now re-emit code instead of FINAL) — but the re-emitted
  code is **byte-identical to their previous candidate, at T=0.7** (stop=converged).
  Conditioned on its own answer + measurements, the champion's posterior collapses onto
  its previous script; only a hard exec error (stderr) forces an actual change
  (0cb7362e again 0 → 0.970 in 2 repair rounds). Refinement is structurally dead for
  this RFT-sharpened model regardless of elicitation; the loop's value on it is
  exec-failure repair. Full run proceeds to quantify exactly that (plus any rare
  revisions on the other 88 samples).
- Full-run config: checklist feedback, T_loop=0.7/top-p 0.95, renders ON (multi-image is
  clean), max-rounds 8, 16 workers stride 16, convergence/FINAL/no-code/budget stops.
