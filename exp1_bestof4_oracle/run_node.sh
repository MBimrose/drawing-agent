#!/bin/bash
# Exp 1 node launcher: 8 single-GPU workers on this box.
#   usage: run_node.sh <base_worker> [stride]
#   wpk-serv-06: run_node.sh 0    (workers 0-7)
#   wpk-serv-05: run_node.sh 8    (workers 8-15)
# Self-contained tree at /srv/scratch/bimrose2/drawing_agent_exp1 (weights,
# eval cache, GT meshes, copied train_v14 code, pinned env mirroring the
# cluster .venv: torch 2.13.0+cu130 / transformers 5.15.1 / build123d 0.11.1).
set -u
D=/srv/scratch/bimrose2/drawing_agent_exp1
export DRAWING_VLM_TRAIN=$D/train_v14
export DRAWING_VLM_EVAL_CACHE=$D/wds_dataset/eval_cache_v14.pkl
export DRAWING_VLM_TRACES_JSON=$D/wds_dataset/traces_v14.json
export DRAWING_VLM_TARS=$D/wds_dataset/tars_v14
export DRAWING_VLM_BAD_KEYS=$D/wds_dataset/exec_bad_keys_v14.txt
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

BASE=${1:?base worker id (0 on serv-06, 8 on serv-05)}
STRIDE=${2:-16}
mkdir -p "$D/out_bo4_oracle" "$D/logs"
for i in $(seq 0 7); do
  W=$((BASE + i))
  CUDA_VISIBLE_DEVICES=$i nohup "$D/env/bin/python" "$D/bo4_oracle_eval.py" \
    --run e24-rft \
    --ckpt "$D/consolidated-checkpoint-3250" \
    --model-base "$D/models/Qwen3.8-27B" \
    --n 96 --k 4 --temperature 0.7 --batch 8 \
    --worker "$W" --stride "$STRIDE" \
    --out "$D/out_bo4_oracle" \
    > "$D/logs/w$(printf %02d "$W").log" 2>&1 &
  echo "worker $W -> GPU $i (pid $!)"
done
