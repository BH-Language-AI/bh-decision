#!/bin/bash
#SBATCH --job-name=bh-grana-p-v2
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-task=1
#SBATCH --time=02:30:00
#SBATCH --output=bh-grana-p-v2-%j.out
# BH-Decision Grana P v2 — Ministral-3-3B-Base + LoRA bf16, expanded-v2 + held-out.
# Upotreba: sbatch grana-p-v2.sbatch <job-dir-na-scratchu>
# (job-dir sadrzi train_grana_p.py + data/{expanded-v2,heldout})
set -euo pipefail
JOBDIR="${1:?upotreba: sbatch grana-p-v2.sbatch <job-dir>}"
module purge
module load Local-LAIF lumi-aif-singularity-bindings
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export PYLIBS=/scratch/project_465003647/agentmujo/pylibs
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export SINGULARITYENV_HF_HUB_CACHE="$HF_HUB_CACHE"
export SINGULARITYENV_PYTHONPATH="$PYLIBS"
mkdir -p "$PYLIBS" "$HF_HUB_CACHE"
srun -n1 singularity exec "$SIF" env PYTHONPATH="$PYLIBS" python -c \
  "import torch; assert 'rocm' in torch.__version__, torch.__version__; print('ROCM-TORCH-OK', torch.__version__)"
cd "$JOBDIR"
srun --unbuffered singularity exec -B "$JOBDIR:/job" -B /scratch:/scratch "$SIF" \
  python -u /job/train_grana_p.py --data /job/data --out /job/out
echo TRAIN_DONE
