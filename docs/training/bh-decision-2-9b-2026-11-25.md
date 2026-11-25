# BH-Decision-2-9B pokušaj 1 (2026-11-25, LUMI job 24030270)

- Plan: EuroLLM-9B + recept A (r32/rsLoRA/cosine/1024, 4 epohe, mix v10),
  BATCH=2/GRAD_ACC=16 zbog VRAM-a, job dir `bh2-9b-v1`.
- Ishod: job pao za ~10 min — `utter-project/EuroLLM-9B` je gated repo,
  403 i lokalno (shaban2024) i na LUMI-ju. Niko nema pristup.
- Bloker: ljudski klik na https://huggingface.co/utter-project/EuroLLM-9B
  (gated:auto — odobrenje bi trebalo biti automatsko). Nakon toga retry istom komandom.
- Fallback (samo uz odobrenje): `Qwen3.5-9B` je već u LUMI hfcacheu, ali Qwen kao
  baza krši roadmap-pravilo ("nikad temelj produkcijskog modela") — samo kao ablacija.
