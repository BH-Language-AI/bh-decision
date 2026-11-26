# BH-Decision-2-9B (2026-11-25/26, LUMI)

## Pokušaj 1 — EuroLLM-9B (job 24030270): BLOKIRAN
- EuroLLM-9B je gated, 403 i lokalno i na LUMI-ju. Čeka ljudski klik.
- Job dir `bh2-9b-v1` ostaje spreman za retry kad pristup prođe.

## Pokušaj 2 — Ministral-3-8B (job 24040475, 26.11.2026): ZAVRŠEN
- Baza: `mistralai/Ministral-3-8B-Base-2512` (EU, Apache-2.0, nije gated —
  ista familija kao Linija-1 pilot na 3B). Metodološki čišće od Qwen fallbacka.
- Recept A (r32/rsLoRA/cosine/1024, 4 epohe, mix v10),
  BATCH=2/GRAD_ACC=16 zbog VRAM-a, job dir `bh2-9b-v1m`.
- Metrike (26.11, TRAIN_DONE): val_loss **0.493**, format_valid_rate **0.65**,
  heldout_accuracy (generativna proba) 0.167 — generacija slaba kao i kod 4B/2B, čeka readout.
- Adapter: `bh2-9b-v1m/out/adapter/` (429 MB) → povučen lokalno, readout eval u toku.

- Plan: EuroLLM-9B + recept A (r32/rsLoRA/cosine/1024, 4 epohe, mix v10),
  BATCH=2/GRAD_ACC=16 zbog VRAM-a, job dir `bh2-9b-v1`.
- Ishod: job pao za ~10 min — `utter-project/EuroLLM-9B` je gated repo,
  403 i lokalno (shaban2024) i na LUMI-ju. Niko nema pristup.
- Bloker: ljudski klik na https://huggingface.co/utter-project/EuroLLM-9B
  (gated:auto — odobrenje bi trebalo biti automatsko). Nakon toga retry istom komandom.
- Fallback (samo uz odobrenje): `Qwen3.5-9B` je već u LUMI hfcacheu, ali Qwen kao
  baza krši roadmap-pravilo ("nikad temelj produkcijskog modela") — samo kao ablacija.

## Pokušaj 3 — Qwen3.5-9B (job 24047633 small-g, 26-27.11.2026): ZAVRŠEN
- Baza `Qwen/Qwen3.5-9B` (otvorena, Apache-2.0). Recept A, mix v10.
- Metrike: val_loss **0.388** (najbolji fit dosad), format **0.55**,
  generativna proba 0.40.
- Readout (vjerni scorer, validiran 17/19 na vA, LUMI GPU):
  **stock 18/19 — tuned 18/19 (paritet)**. Jedini promašaj obje: 013 strukturni.
  Kalibracija: stock Brier 0.006 / ECE 0.067; tuned Brier 0.008 / ECE 0.078.
- Zaključak: baza je već jaka (18/19); LoRA ne dodaje ništa na readoutu
  (unutar šuma, kalibracija nijansu slabija). Objavljuje se iskreno kao
  paritet, ne kao dobitak.
- ISPRAVAK ranijih brojki: stock 4/19 (CPU fp16 artefakt) i Ministral 7/19
  (stari NLL scorer, CPU) su NEVAŽEĆI — multimodalni fp16 na CPU-u daje smeće.
  Ministral-8B nikad nije vjerodostojno izmjeren; tvrdnja "recept ne radi na
  Ministralu" se povlači.
