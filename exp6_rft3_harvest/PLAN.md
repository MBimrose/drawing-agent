# Exp 6 — Kimi K3 teacher pass on the RFT train-pool rejects (rft_v3 seed harvest)

**Question:** exp4 showed Kimi+loop passes the STaR gate on ~1/3 of champion-hard parts and
solves parts the champion cannot. Run the teacher on the TRAIN-POOL REJECTS — parts the
fine-tuned generator failed during RFT rejection sampling — and harvest verified plan+code
trajectories as the `rft_v3` seed. Headline: acceptance rate on rejects (exp4 predicts ~30%),
cost per accepted trajectory, projected economics for the full reject pool.

**CONTAMINATION RULE respected by construction:** the pool is `seen − accepted` from the
cluster's RFT generation over tars_v14 TRAIN shards; eval residues (uuid%50==0 manifest eval,
uuid%50==7 legacy holdout) are excluded twice (rft_generate already skips them; we re-filter
defensively). Nothing from the frozen 96 / eval_cache_v15 enters the batch.

## Reject pool identity

- **Round:** `rft_v2` (most recent; rft_v1 generator = e16-final is stale).
- **Generator:** `e22-combined` `geom_eval/consolidated-checkpoint-3500` (verified from the
  live slurm submit line: `RFT_CKPT=.../runs/e22-combined/geom_eval/consolidated-checkpoint-3500,
  RFT_RUN=e22-combined, RFT_OUT=.../rft_v2`; jobs 10182728/10182729, 2×8 workers, stride 16,
  T=0.6, min-iou 0.8, batch 8, max 2400 new tokens — single draw per key).
  DATA_SOURCES.md concurs ("rft_v2 (generator e22-ckpt3500)"). NOTE: the champion proper is
  e24-rft(=e22+rft_v1 data); rft_v2 rejects are e22-ckpt3500's rejects — the closest
  train-pool reject set that exists, and the one rft_v3 would be built on.
- **Snapshot:** the generation jobs were still RUNNING at pull time (23h into a 24h wall) —
  `seen-*.jsonl` totals 133,048 / `accepted-*.jsonl` 60,472 (45.5% acceptance) at
  2026-08-28 ~10:47 CDT. We snapshot the jsonls once; the pilot selection below only uses
  early shards every worker finished long ago, so the batch is stable under re-snapshot.

## Pipeline

1. **Pull (cluster = data source only):** `rft_v2/seen-*.jsonl` (~10 MB), filter files
   `exec_bad_keys_v14.txt`, `legacy_keys_v14.txt`, `unplaced_keys_v14.txt`, and only the
   tar shards the pilot needs (~25 MB each, ~200 samples/shard).
2. **Rejects & filters** (`select_batch.py`): reject = seen key with iou < 0.8. Exclude
   exec-bad ∪ legacy ∪ unplaced keys and any uuid with residue 0 or 7 mod 50
   (uuid = key.rsplit("_v",1)[0], int(uuid[:8],16) — data_v14.py semantics).
3. **Sampling rule (reproducible/extendable):** take the tars_v14 shards in sorted filename
   order; keep every eligible reject key in (shard, key) sorted order; stop when 300 keys
   are selected; pull exactly the shards touched. Extension = continue in the same order.
   All 16 workers stream their sorted shard slice (shards[w::16]) and are ~35% through, so
   the first few hundred shards are fully seen — verified by checking selected keys appear
   in seen.
4. **Local GT:** extract png + GT .py per selected key; execute GT →STEP→STL with the exp4
   exec harness (/software/python-3.11.1, build123d 0.10 — same env exp4 scored with).
   GT that fails locally: drop key, log it.
5. **Teacher:** Kimi K3 + exp4 FIXED harness verbatim semantics (12-call budget,
   measurement-only feedback, no GT, FINAL only in last 300 chars of <2000-char reply,
   T=0.6, max_tokens 16000). Smoke 5 parts at concurrency ≤4 on the hub router AND on the
   direct vLLM endpoint (wpk-serv-07:8000/v1, openai-completions, needs image support
   verified); pick the faster empirically. Per-part checkpointing (results jsonl append +
   trajectory json per part); long run detached under setsid.
6. **Acceptance:** IoU_centered ≥ 0.8 → `{key, iou, think, code}` records packable by
   pack_rft_shards.py (think = cleaned plan sections of the trajectory, matching the
   traces_v14 style collate_v14.build_messages expects in reasoning_content). Near-misses
   0.5≤IoU<0.8 logged separately. Everything stays local; RESULTS.md gives the rsync the
   user would run to stage rft_v3 on the cluster.

## Layout

- code: `exp6_rft3_harvest/harness/` (+ verbatim exec_harness/iou/inspect_candidate from exp4)
- small results: `exp6_rft3_harvest/` (results.jsonl, accepted/, RESULTS.md)
- bulky: `/srv/scratch/bimrose2/drawing_agent_exp6/` (tars, pngs, GT stls, run dirs) and
  `exp6_rft3_harvest/artifacts/` (gitignored)

## Progress log

- [x] Docs read; harness + conventions understood; tunnel verified
- [x] rft_v2 identified (generator e22-ckpt3500 via live slurm submit line); pool measured:
      133,048 seen / 60,472 accepted at snapshot
- [x] jsonls + filter files pulled; rejects computed: 72,693 rejects, **46,125 eligible**
      after filters (26,568 unplaced removed; exec-bad/legacy/eval already absent —
      rft_generate filtered them at generation). Eligible reject gen-IoU: mean 0.302,
      median 0.226, 43% exact 0.0 (exec/no-code failures), 16,444 near-miss 0.5–0.8.
- [x] pilot batch selected: 300 keys = all eligible rejects of the first 6 sorted shards
      (shard_000000/02/04/18/21/22, 46–63 per shard); 8 shards pulled (2 spare margin)
- [x] GT exec locally verified: 299/300 usable (1 GT failure dropped, logged)
- [x] direct endpoint verified: serv-07:8000/v1 serves moonshotai/Kimi-K3, accepts
      image_url data URIs, auth via ~/.claude-hub/serv08.key (SERVER7_API_KEY value);
      reasoning arrives in a separate `reasoning` field, content is clean
- [x] smoke_direct done (5 parts, 4 workers): 1 gate pass (00015daa gen 0.0 → **0.883**),
      1 near-miss 0.793, mean 2.9 calls, mean 291 s/part, longest 469 s; one no_code
      failure (61k-char runaway deliberation in the content channel × 3 — exp4's known
      failure class, correctly not FINAL'd). Endpoint answered 4-way concurrency cleanly.
- [x] smoke_router same 5 parts: **router loses decisively** — 2/5 parts DIED on
      HTTP 502 "upstream unreachable" after 4 retries (the exp3/exp4 router flakiness),
      completed parts mean 1161 s vs 228 s direct on the same keys (~5×), quality paired
      n=3: router 0.465 vs direct 0.452 (noise). → MAIN RUN ON THE DIRECT ENDPOINT.
- [ ] main harvest: 299 parts, 6 workers, direct endpoint — launched detached (setsid,
      log /srv/scratch/bimrose2/drawing_agent_exp6/logs/main_run.log), resume-safe;
      smoke-based projection ~291 part-serial s → ~4–6 h wall at 6 workers
- [ ] N/300 harvested
- [ ] packed + RESULTS.md
