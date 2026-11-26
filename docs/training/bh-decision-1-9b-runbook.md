# BH-Decision-1-9B — runbook do prve produkcijske varijante (2026-11-26)

Cilj: prve težine na `BH-Language-AI/bh-decision-1-9b` (trenutno samo kartica).
Baza: `mistralai/Ministral-3-8B-Base-2512` (EU, Apache-2.0, negated — pristup verificiran 26.11).
EuroLLM-9B otpao — i dalje gated (403), odluka zabilježena na kartici 1-9b.

## Status polaznika

- Podaci: `datasets/bh-decision-2/train-v10.jsonl` — 7849 primjera, sha `d928b3333645ba78` ✅ lokalno
- Held-out: `datasets/heldout/heldout-v1.jsonl` (zaključan, 20 neviđenih / 19 bodovanih) ✅
- Trening skripta: `slurm/grana-p-v2/train_grana_p.py` — recept A preko env-a ✅
- Prethodni job: 24040475 (26.11, job dir `bh2-9b-v1m`, Ministral + recept A) — status NEPOZNAT (nema LUMI pristupa)
- Recept A (provjeren na 4B → 18/19 readout): `LORA_R=32 LORA_ALPHA=64 RS_LORA=1 SCHEDULER=cosine WARMUP=0.1 LR=1e-4 EPOCHS=4 MAX_LEN=1024 BATCH=2 GRAD_ACC=16`

## Blokeri (ljudske akcije, ne mogu sam)

1. **EFP cert istekao** — refresh na https://sshca.my-eurohpc.eu (vrijedi ~1h), host `lumi-efp`.
2. Ako EuroLLM-9B ikad zatreba: klik-odobrenje na https://huggingface.co/utter-project/EuroLLM-9B (ne blokira 1-9b — Ministral je odluka).

## Koraci (nakon cert refresh-a)

```bash
# 1. Status starog joba
ssh lumi-efp "sacct -j 24040475 --format=JobID,State,Elapsed,ExitCode | head"
ssh lumi-efp "ls /scratch/project_465003647/agentmujo/bh2-9b-v1m/out/adapter 2>/dev/null"
# 2a. Ako TRAIN_DONE + adapter postoji → na korak 3.
# 2b. Ako FAILED → log: ssh lumi-efp "tail -n 30 /scratch/.../bh2-9b-v1m/*.out"; retry istim sbatchom.
# 2c. Ako nikad nije ni krenuo → provjeri red: squeue -u $USER; po potrebi resubmit (small-g, --time 12:00:00,
#     9B/7849 uz eff.batch 32 ≈ 1000 koraka/epoha — dev-g 2:30 NEĆE stati).
# 3. Eval na LUMI-ju (GPU): generacijski harness nad held-out v1, strogo + tolerantno + format;
#    cilj: iznad 4B v0.5-rc (generacija 6/19 tol., format 18/20). Adapter se NE objavljuje ispod stocka.
# 4. Lokalni smoke (CPU): download adaptera, load + 1 held-out uzorak end-to-end.
# 5. Objava: hf upload adapter (+tokenizer/chat_template) na bh-decision-1-9b; kartica: brojke + datum;
#    kolekcija bh-decision: note "Gen 1 9B — OBJAVLJEN, x/19".
```

## Pravila objave (bez izuzetka)

- Bez fabriciranja: samo mjereni brojevi; held-out NIKAD u treningu (train-v10 vs heldout-v1 preklapanje = 0 — provjereno ranije).
- Adapter Apache-2.0; baza Ministral-3-8B-Base-2512 (Apache-2.0, EU) — kartica to navodi.
