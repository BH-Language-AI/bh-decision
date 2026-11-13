# Grana P — Ministral pilot (2026-11-13, Kaggle T4)

> Korak 1 FAZE 5b: prva provjera EU baze dokazom. Bez destilacije, bez tuđih izlaza.

## Postavka

- Baza: `mistralai/Ministral-3-3B-Base-2512` (3.8B, Mistral AI, Apache-2.0, bf16, čisti tekst
  kroz `AutoModelForImageTextToText` — multimodalna arhitektura, vision tower nekorišten).
- Podaci: `datasets/expanded` (400, 8×50, ijekavica), split 360/40, isti `state + "\nODLUKA: " + reference` format kao pilot B.
- Recept: QLoRA nf4 + double quant (T4 14.5GB ne drži fp16 full-gradijente — dokazano OOM v4/v5),
  r16, fp16 compute, 3 epohe, batch 1×32, max_length 512, seed 42.
- Kernel: `admiragic/bh-decision-ministral-pilot` v6 (v1–v5: transformers prestari → multimodalna
  klasa → torchao → OOM fp16; sve dokumentirano u kernel logu).

## Rezultat

- `val_loss: 0.804` (40 val), `format_valid_rate: 1.0` (5/5 proba, validan JSON s `decision`+`confidence`).
- Generacije uče format, ali rationale je šablonski (ponavlja se) — znak da 400 primjera uči
  formu, ne rasuđivanje. Za usporedbu: pilot B (EuroLLM-1.7B) val 0.491, format 0.4 (odsijecanje na 128 tokena).

## Zaključak

- Pipeline na Ministral-3-3B radi end-to-end na T4 (QLoRA). Baza je legitimna EU opcija.
- Sljedeće: veći i raznovrsniji bosanski dataset (Korak 1 se nastavlja) + ljudska validacija
  uzorka prije sljedećeg runa. Adapter neobjavljen.
