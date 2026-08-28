# drawing-agent

Agentic-harness experiments for the drawing→STEP project ([drawing-vlm](https://github.com/MBimrose/drawing-vlm)).
Decides whether (1) critic-reranked best-of-N and (2) an agentic data engine are worth building.

| Experiment | Question | Where it runs |
|---|---|---|
| [exp1_bestof4_oracle](exp1_bestof4_oracle/) | How much IoU does "first-executing draw" leave on the table vs the oracle-best of 4 draws? (= ceiling for a critic reranker) | Campus cluster (e24-rft checkpoint + eval pool live there) |
| [exp2_agentic_spike](exp2_agentic_spike/) | Does an agentic loop with geometry feedback beat single-shot on hard drawings? (= case for the STaR data engine) | wpk-serv-06 (fresh drawings generated with step_to_drw) |

`vendor/` holds read-only reference clones (gitignored): drawing-vlm, step_to_drw.

Background: analysis session 2026-08-27 — cadgenbench-build123d lessons (dimension-chain prompting,
two-tier validity gates, PASS-tool trap), deepseek-harness capabilities, and the current
drawing-vlm state (e24-rft: 0.876 IoU best-of-4+repair, STaR loop). See `docs/context.md`.
