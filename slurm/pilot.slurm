#!/bin/bash
#SBATCH --job-name=bh-pilot
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
# TODO: postaviti particiju (npr. --partition=gpu).
#SBATCH --partition=TODO-particija
# TODO: postaviti racun/projekat (npr. --account=projekt123).
#SBATCH --account=TODO-racun
# TODO: postaviti zidno vrijeme (npr. A: 02:00:00, B: 04:00:00, C: 08:00:00).
#SBATCH --time=TODO-08:00:00
# TODO: postaviti krak: a, b ili c.
#SBATCH --export=PILOT_ARM=a

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"

OUT="${SCRATCH:-$PWD}/bh-pilot-$PILOT_ARM-$SLURM_JOB_ID"
mkdir -p "$OUT/checkpoints" "$OUT/preds"

export BH_DECISION_ALLOW_TRAIN=1
python3 scripts/pilot.py --arm "$PILOT_ARM" --no-dry-run --confirm
python3 benchmarks/harness.py --ref datasets/samples/benchmark.jsonl \
  --pred "preds/${PILOT_ARM}.jsonl" | tee "$OUT/eval-$PILOT_ARM.json"

cp -r "checkpoints/pilot-$PILOT_ARM" "$OUT/checkpoints/" 2>/dev/null || true
echo "gotovo: rezultati u $OUT"
