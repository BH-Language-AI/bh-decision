# BH-Decision-2-9B (2026-11-25/26, LUMI)

## Pokušaj 1 — EuroLLM-9B (job 24030270): BLOKIRAN
- EuroLLM-9B je gated, 403 i lokalno i na LUMI-ju. Čeka ljudski klik.
- Job dir `bh2-9b-v1` ostaje spreman za retry kad pristup prođe.

## Pokušaj 2 — Ministral-3-8B (job 24040475, 26.11.2026)
- Baza: `mistralai/Ministral-3-8B-Base-2512` (EU, Apache-2.0, nije gated —
  ista familija kao Linija-1 pilot na 3B). Metodološki čišće od Qwen fallbacka.
- Recept A (r32/rsLoRA/cosine/1024, 4 epohe, mix v10),
  BATCH=2/GRAD_ACC=16 zbog VRAM-a, job dir `bh2-9b-v1m`.

- Plan: EuroLLM-9B + recept A (r32/rsLoRA/cosine/1024, 4 epohe, mix v10),
  BATCH=2/GRAD_ACC=16 zbog VRAM-a, job dir `bh2-9b-v1`.
- Ishod: job pao za ~10 min — `utter-project/EuroLLM-9B` je gated repo,
  403 i lokalno (shaban2024) i na LUMI-ju. Niko nema pristup.
- Bloker: ljudski klik na https://huggingface.co/utter-project/EuroLLM-9B
  (gated:auto — odobrenje bi trebalo biti automatsko). Nakon toga retry istom komandom.
- Fallback (samo uz odobrenje): `Qwen3.5-9B` je već u LUMI hfcacheu, ali Qwen kao
  baza krši roadmap-pravilo ("nikad temelj produkcijskog modela") — samo kao ablacija.
