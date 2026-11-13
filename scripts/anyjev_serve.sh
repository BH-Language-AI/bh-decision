#!/bin/bash
# Napredna verzija: dize lokalni AnyJev bridge (Tacit-4B, CPU) na 127.0.0.1:8101.
# Bez downloada ako je model vec kesiran (HF_HUB_OFFLINE=1).
# Override: ANYJEV_VENV, ANYJEV_MODEL, ANYJEV_PORT. Bez auth — samo localhost.
set -e
VENV=${ANYJEV_VENV:-/home/sha/.venvs/anyjev/bin/python}
MODEL=${ANYJEV_MODEL:-morriszjm/Tacit-4B}
PORT=${ANYJEV_PORT:-8101}
exec env HF_HUB_OFFLINE=1 "$VENV" "$(dirname "$0")/anyjev_bridge.py" \
  --model "$MODEL" --mode tacit --engine transformers --dtype float32 --port "$PORT"
