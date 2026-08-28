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
