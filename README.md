# drawing-agent

Agentic-harness experiments for the drawing→STEP project ([drawing-vlm](https://github.com/MBimrose/drawing-vlm)).
Decides whether (1) critic-reranked best-of-N and (2) an agentic data engine are worth building.

| Experiment | Question | Answer |
|---|---|---|
| [exp1_bestof4_oracle](exp1_bestof4_oracle/) | Oracle-of-4 vs deployed first-exec — reranker ceiling? | +0.047 [CI +0.031..+0.064]; 79% of gap in 18 gross errors → GO |
| [exp2_agentic_spike](exp2_agentic_spike/) | Does an agentic measurement-feedback loop beat single-shot? | Yes: Kimi +0.118 (chained dims +0.149); base-27B +0.600, STaR gate 0→9/20 |
| [exp3_reranker](exp3_reranker/) | Can selection policies close the oracle gap? | Heuristic rerank **0.876→0.898** [CI +0.009..+0.038], 0 model calls; VLM critic NOT significant |
| [exp4_frontier_vs_finetune](exp4_frontier_vs_finetune/) | Does frontier+harness compare to the fine-tune on its own eval? | No: Kimi+loop 0.724 vs deployed 0.876 — but max(both)=0.919≈oracle → teacher for the stuck tail |
| [exp5_champion_loop](exp5_champion_loop/) | Does the loop stack on top of fine-tuning? | No: 0.818 vs 0.876; revision mode-collapsed, fresh draws beat conditioned repair |
| [exp6_rft3_harvest](exp6_rft3_harvest/) | Can Kimi+loop harvest an rft_v3 seed from the train-pool rejects? | Yes: 75/299 rejects pass the STaR gate (25.1%, accepted mean 0.921, 38 from gen-IoU-0.0 parts); direct vLLM endpoint ~5× faster than the hub router, 0 transport losses |

**Frozen-96 ladder (centered IoU):** Kimi ss 0.549 → Kimi+loop 0.724 → champ greedy 0.787 →
champ+loop 0.818 → champ bo4+repair 0.876 → **champ bo4+rerank 0.898 (deployable record)** → oracle 0.922.

Benchmark design for the next cycle: [docs/benchmark_strategy.md](docs/benchmark_strategy.md) (v2 final).

`vendor/` holds read-only reference clones (gitignored): drawing-vlm, step_to_drw.

Background: analysis session 2026-08-27 — cadgenbench-build123d lessons (dimension-chain prompting,
two-tier validity gates, PASS-tool trap), deepseek-harness capabilities, and the current
drawing-vlm state (e24-rft: 0.876 IoU best-of-4+repair, STaR loop). See `docs/context.md`.
