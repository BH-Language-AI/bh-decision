#!/bin/bash
#SBATCH --job-name=bh-eval-9b
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-task=1
#SBATCH --time=03:00:00
#SBATCH --output=bh-eval-9b-%j.out
# BH-Decision 9B eval — stock vs adapter, isti prompt/metrika kao in-train proba.
# Upotreba: sbatch eval-9b.sbatch <eval-dir> <job-dir-bh2-9b-v1m> [model-hf-id]
set -euo pipefail
EVALDIR="${1:?upotreba: sbatch eval-9b.sbatch <eval-dir> <job-dir> [model]}"
JOBDIR="${2:?nedostaje job-dir s adapterom i data/heldout}"
MODEL="${3:-mistralai/Ministral-3-8B-Base-2512}"
module purge
module load Local-LAIF lumi-aif-singularity-bindings
export SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
export PYLIBS=/scratch/project_465003647/agentmujo/pylibs
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export SINGULARITYENV_HF_HUB_CACHE="$HF_HUB_CACHE"
export SINGULARITYENV_PYTHONPATH="$PYLIBS"
cd "$EVALDIR"
run() {
  srun --unbuffered singularity exec -B "$EVALDIR:/job" -B /scratch:/scratch "$SIF" \
    env PYTHONPATH="$PYLIBS" EVAL_NO_CACHE=1 python -u /job/eval_9b.py --model "$MODEL" "$@" --heldout /job/data-heldout-link --out /job/out
}
mkdir -p "$EVALDIR/out"
ln -sfn "$JOBDIR/data/heldout/heldout-v1.jsonl" "$EVALDIR/data-heldout-link"
run --adapter ""
run --adapter "$JOBDIR/out/adapter"
echo EVAL_DONE
