#!/bin/bash
#SBATCH --job-name=exp1-bo4-oracle
#SBATCH --account=wpk
#SBATCH --partition=wpk
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --nodelist=ccc0442
#SBATCH --gres=gpu:L40S:4
#SBATCH --mem=500G
#SBATCH --time=24:00:00
#SBATCH --output=/projects/illinois/eng/ece/wpk/bimrose2/drawing_agent_exp1/logs/%x.o%j
#SBATCH --error=/projects/illinois/eng/ece/wpk/bimrose2/drawing_agent_exp1/logs/%x.e%j

# Exp 1 (drawing-agent): all-draws best-of-4 with per-draw IoU scoring on
# e24-rft checkpoint-3250. Conventions (account/partition/node/gres) copied
# from drawing-vlm train_v14/sbatch/geom_eval.sbatch (ccc0442: ccc0441 has a
# bad L40S). One-shot job — no self-resubmission. Writes ONLY under
# drawing_agent_exp1/; read-only against drawing_vlm/.
set -uo pipefail
ROOT=/projects/illinois/eng/ece/wpk/bimrose2/drawing_vlm
EXP=/projects/illinois/eng/ece/wpk/bimrose2/drawing_agent_exp1

source "$ROOT/.venv/bin/activate"
source "$ROOT/train_v14/env.sh"

python "$EXP/bo4_oracle_eval.py" \
  --run e24-rft \
  --ckpt "$ROOT/runs/e24-rft/geom_eval/consolidated-checkpoint-3250" \
  --n 96 --k 4 --temperature 0.7 --batch 8 \
  --out "$EXP/out_bo4_oracle"
