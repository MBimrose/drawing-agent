# Shared context (2026-08-27)

## The project
drawing-vlm fine-tunes Qwen3.8-27B: drawing PNG → `<think>` construction plan + fenced build123d
script → executed → STEP → STL → **centered volumetric IoU** vs GT (metric:
`vendor/drawing-vlm/train_v14/geom/iou.py`, exec: `geom/exec_harness.py`).
Frozen 96-sample eval pool (uuid%50==0). Seed noise ±0.03–0.05 IoU.

Current record (e24-rft ckpt-3250, `results/e24-rft.bestof4-checkpoint-3250.json`):
**0.876 mean IoU / 99% exec** under best-of-4 + 2 repair rounds; 0.795 greedy+repair; 0.759 e22.
Best-of-4 policy: draw 0 greedy, draws 1–3 at T=0.7/top_p 0.95, keep the **first that executes**
(no quality ranking) — see `train_v14/geom/bestofn_eval.py`. coverage_by_draw for e24:
draw0 85/96, +8, +2, 1 unsolved.

The campus-cluster "reinforcement loop" is STaR/RFT (`train_v14/geom/rft_generate.py`):
sample champion at T=0.6, accept IoU≥0.8, mix back into SFT (~40–45% acceptance).

## Infrastructure facts
- This box is **wpk-serv-06** (8×H200, currently idle). Qwen3.6-27B server on :8000 is stopped.
- **Campus cluster**: `ssh cc-login` (ControlMaster auto, ControlPersist 12h,
  socket `~/.claude-hub/cm-cc-*`). Project dir:
  `/projects/illinois/eng/ece/wpk/bimrose2/drawing_vlm`.
  **STANDING RULE (user, 2026-08-27): the cluster is a data source ONLY — file pulls
  (rsync/scp) and trivial ls/find over the tunnel are fine, but NO sbatch jobs and no heavy
  login-node compute. All experiment compute runs on wpk-serv-05 and wpk-serv-06
  (8×H200 each; serv-05 /srv/scratch has ~52T free).**
- **Endpoints**: GLM-OCR at wpk-serv-11:8000 (up, vision, OCR-specialized). Hub router
  (anthropic-messages) at wpk-serv-07.mechse.illinois.edu:3456 — models incl.
  `claude-moonshotai/Kimi-K3[1m]`, `claude-qwen3.8-27b`, `claude-qwen36-27b-build123d-critic`;
  auth via `KING_API_KEY` env (see `~/.dsh/settings.yaml`). Kimi K3 direct vLLM:
  serv-07:8000/v1 (its /v1/models returns an empty list but the server answers — verify with a
  completion). Kimi K3 vision support: **unverified** — test before relying on it.
- **VLM option**: `/srv/scratch/bimrose2/serve_qwen3_vl_235b.sh` relaunches Qwen3-VL-235B-NVFP4
  on :8002 (use `vllm_env_sm90`; the Kimi-co-location/MPS notes in it are obsolete — Kimi is
  stopped, so it can run alone WITHOUT MPS and `--gpu-memory-utilization` can go to ~0.90).
  Check port free first; log under /srv/scratch/bimrose2/serve_logs/.
- **dsh** (deepseek-harness 0.1.1-rc.2) installed; config `~/.dsh/settings.yaml`. For image input
  on a self-hosted route, the model entry must declare `input: [text, image]`. Headless:
  `dsh --profile headless "task"`. Python SDK: `profile="sdk"` (NOT sdk-minimal — no image tools).
- **build123d-mcp** (pzfreo) checkout: `/srv/scratch/bimrose2/build123d-mcp`.
- **Python**: `/srv/scratch/bimrose2/mcp_env/bin/python` has build123d 0.11.1. Make your own venv
  for extra deps (manifold3d, trimesh, ...). Scoring deps mirror `vendor/drawing-vlm` geom code.
- GitHub: `gh` authed as MBimrose; push to this repo is expected.

## cadgenbench-build123d lessons to apply (measured, from pzfreo's repo)
- **Dimension-chain prompting**: classify stacked dims overall-vs-component, name both extension-line
  endpoints, one arithmetic chain per axis, cross-check bbox against other views. (+0.024 mean,
  +0.33 on affected fixtures. Dimension *inference* is the bottleneck: same part re-dimensioned
  indirectly dropped GPT-5.5 0.93→0.63.)
- **Named-parameter block**: every dimension a named variable with unit comment; derived values by
  formula; never inline numbers.
- **Priority order with cost model**: absolute size ≫ feature set ≫ overall form ≫ fillets/chamfers.
- **Two-tier validity gate**: cheap in-loop validate; authoritative exact mesh check out-of-process
  on the written STEP (the fast in-process check can silently pass broken parts).
- **PASS-tool trap**: any tool whose output reads as "conforms/PASS" becomes a stop signal the model
  obeys despite prompt caveats. Phrase check-tool outputs as measurements, not verdicts.
- **Anti-patterns**: no edge-detection/contour-tracing of the drawing; render to *compare* after a
  change, ≤1 render per view per pass; don't grid-sample is_inside().
- **Checkpoint-first**: get any valid solid exported early, never overwrite a passing artifact with
  an unproven one.
- Run isolation: execute agent work in a temp dir outside the repo; mirror artifacts back.

## Repo conventions
- Each experiment writes ONLY inside its own `exp*/` dir. Commit with `git add <your-dir>`;
  `git pull --rebase` before push; retry on index-lock races.
- Keep large artifacts (STLs, PNGs > a few MB, model outputs en masse) out of git or in
  `exp*/artifacts/` behind .gitignore; commit result tables/JSON summaries and code.
- Progress notes in `exp*/PLAN.md`, final numbers + verdict in `exp*/RESULTS.md`.
