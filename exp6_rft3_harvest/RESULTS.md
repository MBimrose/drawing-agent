# Exp 6 results — Kimi K3 teacher harvest on the RFT train-pool rejects (rft_v3 seed)

**Date:** 2026-08-28 · **Teacher:** Kimi K3 (direct vLLM, wpk-serv-07:8000) + the exp4
FIXED agentic harness (12-call budget, measurement-only feedback, no GT, FINAL-in-tail
detector) · **Metric:** centered volumetric IoU vs locally-rebuilt GT STLs, gate ≥ 0.8
(the rft_generate acceptance rule).

## TL;DR

**On 299 parts the fine-tuned generator failed during RFT rejection sampling, Kimi+loop
passes the STaR gate on 75 = 25.1% (accepted mean IoU 0.921), plus 106 near-misses
(0.5–0.8).** 38 of the 75 accepted come from parts where the generator produced NOTHING
usable (gen IoU exactly 0.0). Exp4's eval-pool prediction (~30% of champ-hard) transfers
to the training pool essentially unchanged. The harvest is checkpointed, reproducible,
and extendable; the 75-record `accepted_rft_v3_seed.jsonl` is packable by the vendor
`pack_rft_shards.py` as-is. Measured economics: **~49 teacher part-minutes / ~0.6 M
tokens per accepted trajectory**; the full 46k-part reject pool would yield ~11.6k
trajectories in ~44 single-server days at the measured 8-way rate (see scaling below).

## The reject pool (identity + filters)

- **Round:** `rft_v2`, generator `e22-combined/geom_eval/consolidated-checkpoint-3500`
  (read off the live slurm submit line of jobs 10182728/9; DATA_SOURCES.md concurs).
  Single draw per key at T=0.6, accept IoU≥0.8. NOTE: the deployed champion is e24-rft
  (= e22 + rft_v1 data); rft_v2's rejects are e22-ckpt3500's rejects — the train-pool
  reject set rft_v3 would actually be built on.
- **Snapshot 2026-08-28 ~10:50 CDT** (generation still running, 23 h into its 24 h
  wall): 133,272 seen / 60,472 accepted (45.4%) → **72,693 rejects**.
- **Filters** (data_v14 semantics): unplaced-dims keys −26,568 (a sheet missing required
  dims is unsolvable from the drawing); exec-bad, legacy-renderer and both eval residues
  (uuid%50∈{0,7}) contributed 0 — rft_generate already excluded them at generation time
  (verified independently). **Eligible pool: 46,125 rejects** — gen IoU mean 0.302,
  median 0.226, 43% exactly 0.0, 16,444 near-misses (0.5–0.8).
- **CONTAMINATION:** all keys are tars_v14 TRAIN keys; eval residues excluded twice.
  Nothing from the frozen 96 / eval_cache_v15 is touched.

## Pilot batch (reproducible sampling rule)

Walk tars_v14 shards in sorted filename order, keys sorted within a shard, keep every
eligible reject, stop at 300: → shards 000000/02/04/18/21/22 (46–63 eligible each).
All 16 generation workers were long past these early shards, so the batch is stable
under re-snapshot. Extension = same walk, larger N (2 spare shards already pulled).
GT rebuilt locally (exec harness → STEP → STL, build123d 0.10 — the same env that
scores the teacher): 299/300 usable, 1 GT failure dropped (`gt_failures.json`).

## Headline table (n=299)

| | mean IoU | STaR gate ≥0.8 | near-miss 0.5–0.8 | exec |
|---|---|---|---|---|
| e22-ckpt3500 (the RFT draw that rejected these) | 0.301* | 0/299 by construction | 105/299 | — |
| Kimi K3 single-shot (turn 1) | 0.138 | 27/299 (9.0%) | — | 178/299 |
| **Kimi K3 + agentic loop** | **0.552** | **75/299 (25.1%)** | 106/299 (35.5%) | 289/299 |

*gen IoU of the pilot keys; single T=0.6 draw, not best-of-N.

- **Accepted quality:** mean IoU 0.921 (min 0.801); mean 3.5 calls; think = full
  dimension-chain reading + revision notes (mean 1.3k chars).
- **Complementarity, again:** 38/75 accepted had gen IoU = 0.0, and the accepted parts'
  mean gen IoU is 0.278 — the teacher is not skimming the almost-solved tail.
- By generator-failure bucket:

| bucket | n | kimi ss | kimi ag | gate | near-miss |
|---|---|---|---|---|---|
| gen 0.0 (exec/no-code fail) | 126 | 0.136 | 0.584 | 38/126 (30%) | 40/126 |
| gen (0, 0.5) | 68 | 0.086 | 0.398 | 10/68 (15%) | 17/68 |
| gen [0.5, 0.8) | 105 | 0.175 | 0.614 | 27/105 (26%) | 49/105 |

The middle bucket is the hardest for everyone — parts the generator got structurally
wrong (not merely broken code) are also the ones Kimi misreads. Champion-executes-badly
and champion-nearly-solves are both fertile; champion-solves-wrongly is not.

- Stop reasons: 275 explicit FINAL, 16 no_code (3× runaway deliberation without a code
  fence — exp4's known failure class, correctly not FINAL'd), 8 budget (12 calls).
- Loop lift decomposition matches exp4: single-shot exec is only 178/299; the loop
  repairs execution to 289/299 and nearly triples gate yield (27 → 75).

## Router vs direct endpoint (paired smoke, same 5 parts, 4 workers)

| key | direct ag | router ag | direct t | router t |
|---|---|---|---|---|
| 00010569 | 0.374 | 0.374 | 41 s | 635 s |
| 0001287b | 0.793 | 0.652 | 401 s | 2667 s |
| 0001b0b1 | 0.191 | 0.370 | 243 s | 180 s |
| 00015daa | 0.883 (gate) | **died: HTTP 502 ×4 retries** | 299 s | — |
| 00007bf3 | 0.000 | **died: HTTP 502 ×4 retries** | 469 s | — |

Direct vLLM (`wpk-serv-07:8000/v1`, openai chat-completions, key = `serv08.key` =
SERVER7_API_KEY; image_url data-URIs verified; Kimi's reasoning arrives in a separate
`reasoning` field, content stays clean) is **~5× faster on completed parts (mean 228 s
vs 1161 s) and lost 0/299 parts to transport errors in the main run, vs 2/5 dead in the
router smoke.** Quality is indistinguishable (paired n=3: 0.452 vs 0.465). Exp3/exp4's
router 502s/degradation are the middlebox, not the model. **All future teacher passes
should use the direct endpoint.**

## Cost / economics (measured, direct endpoint)

- Whole run: 299 parts, 1,251 calls, 33.2 M in / 12.5 M out tokens, 60.9 part-serial h;
  wall ≈ 8.8 h (launched 12:10 CDT at 6 workers ≈ 0.37 parts/min; restarted resume-safe
  16:40 at 8 workers ≈ **0.73 parts/min**, server never queued). Zero errored parts.
- Per part: mean 4.2 calls, 111 k in / 42 k out tokens, 733 part-serial s.
- **Per ACCEPTED trajectory: 16.7 calls, 443 k in / 166 k out tokens, 48.7 part-min
  ≈ 6.8 wall-min at 8 workers.**
- **Full-pool projection (46,125 eligible rejects):** ~11,600 accepted trajectories,
  ~5.1 B in / 1.9 B out tokens, ~44 days on one server at 8-way. Levers, in order:
  (1) concurrency — vLLM had zero queuing at 8; 16–32 way is untested but likely 2–4×
  aggregate; (2) skip the gen(0,0.5) bucket (15% yield vs 30%/26% — saves 23% of pool
  for an 8% yield loss); (3) exp4's union lesson — a second seed pass over the
  *failures* harvests more (union 13→16/24 there), so re-running the 118 no-gate parts
  is worth ~½ the marginal cost of fresh parts per accepted.
- Perspective: 11.6k Kimi trajectories ≈ 19% of rft_v2's 60k self-accepted — but drawn
  entirely from the 55% of the pool the generator cannot learn from at all today.

## Deliverables + handoff

- **`accepted_rft_v3_seed.jsonl`** (committed): 75 records `{key, iou, think, code}` —
  exactly the shape `pack_rft_shards.py` consumes. think = last full (non-revision-
  voiced) plan + `Revision:` paragraphs distilled from the trajectory
  (`harness/distill_pack.py`; re-runnable offline from the stored trajectories).
- `nearmiss.jsonl` (committed): 106 records with think/code + gen_iou/ss_iou for
  analysis (candidate pool for an overlay-critic rescue pass).
- `results_main.jsonl`, `results_smoke_{direct,router}.jsonl` (committed);
  trajectories + run dirs + drawings + GT under `/srv/scratch/bimrose2/drawing_agent_exp6/`
  (local only, per the no-push rule).
- **Staging rft_v3 on the cluster (USER runs this; nothing was pushed):**

```bash
ssh cc-login 'mkdir -p /projects/illinois/eng/ece/wpk/bimrose2/drawing_vlm/rft_v3'
rsync -av /srv/scratch/bimrose2/drawing-agent/exp6_rft3_harvest/accepted_rft_v3_seed.jsonl \
  cc-login:/projects/illinois/eng/ece/wpk/bimrose2/drawing_vlm/rft_v3/accepted-kimi-000.jsonl
# then on the cluster (pulls PNGs from tars_v14 by key, writes rft_v3/shards/):
python train_v14/geom/pack_rft_shards.py \
  /projects/illinois/eng/ece/wpk/bimrose2/drawing_vlm/rft_v3
```

  Note the think voice is Kimi's plan style, not the champion's `<think>` style —
  the e27 pack/collate path consumes it verbatim (STaR precedent: verified rationales
  are trusted); worth an A/B against style-normalized thinks if e28 underperforms.

## Reproduce / extend

```bash
python3 harness/select_batch.py --stats          # pool numbers from the snapshot
python3 harness/select_batch.py --n 300          # pilot selection (needs tars/)
python3 harness/prep_gt.py                       # extract PNGs, build GT STLs
python3 harness/probe_endpoint.py                # verify direct endpoint + image input
python3 harness/run_teacher.py --backend direct --workers 8 --tag main   # resume-safe
python3 harness/distill_pack.py --tag main       # seed jsonl + stats
python3 harness/summarize.py                     # tables incl. router comparison
```

Hygiene: cluster used as data source only (jsonl/filter/tar pulls over the existing
tunnel); all compute on wpk-serv-06 CPUs + the serv-07 Kimi endpoint; wpk-serv-06 GPUs
untouched; generated scripts executed in temp dirs outside the repo.
