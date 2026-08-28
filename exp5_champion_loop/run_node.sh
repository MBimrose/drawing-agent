#!/bin/bash
# Exp 5 node launcher: 8 single-GPU loop workers on this box.
#   usage: run_node.sh <base_worker> [stride] [render]
#   wpk-serv-06: run_node.sh 0    (workers 0-7)
#   wpk-serv-05: run_node.sh 8    (workers 8-15)
# Reads the exp1 self-contained tree READ-ONLY (weights, env, eval assets);
# writes only under /srv/scratch/bimrose2/drawing_agent_exp5.
set -u
D1=/srv/scratch/bimrose2/drawing_agent_exp1
D5=/srv/scratch/bimrose2/drawing_agent_exp5
export DRAWING_VLM_TRAIN=$D1/train_v14
export DRAWING_VLM_EVAL_CACHE=$D1/wds_dataset/eval_cache_v14.pkl
export DRAWING_VLM_TRACES_JSON=$D1/wds_dataset/traces_v14.json
export DRAWING_VLM_TARS=$D1/wds_dataset/tars_v14
export DRAWING_VLM_BAD_KEYS=$D1/wds_dataset/exec_bad_keys_v14.txt
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

BASE=${1:?base worker id (0 on serv-06, 8 on serv-05)}
STRIDE=${2:-16}
RENDER=${3:-on}
mkdir -p "$D5/out_loop" "$D5/logs"
for i in $(seq 0 7); do
  W=$((BASE + i))
  CUDA_VISIBLE_DEVICES=$i nohup "$D1/env/bin/python" "$D5/loop_eval.py" \
    --run e24-rft \
    --ckpt "$D1/consolidated-checkpoint-3250" \
    --model-base "$D1/models/Qwen3.8-27B" \
    --n 96 --max-rounds 8 --batch 8 --render "$RENDER" \
    --worker "$W" --stride "$STRIDE" \
    --out "$D5/out_loop" \
    > "$D5/logs/w$(printf %02d "$W").log" 2>&1 &
  echo "worker $W -> GPU $i (pid $!)"
done
