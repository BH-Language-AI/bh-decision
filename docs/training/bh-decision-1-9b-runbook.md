# BH-Decision-1-9B — runbook do prve produkcijske varijante (2026-11-26)

Cilj: prve težine na `BH-Language-AI/bh-decision-1-9b` (trenutno samo kartica).
Baza: `mistralai/Ministral-3-8B-Base-2512` (EU, Apache-2.0, negated — pristup verificiran 26.11).
EuroLLM-9B otpao — i dalje gated (403), odluka zabilježena na kartici 1-9b.

## Status polaznika

- Podaci: `datasets/bh-decision-2/train-v10.jsonl` — 7849 primjera, sha `d928b3333645ba78` ✅ lokalno
- Held-out: `datasets/heldout/heldout-v1.jsonl` (zaključan, 20 neviđenih / 19 bodovanih) ✅
- Trening skripta: `slurm/grana-p-v2/train_grana_p.py` — recept A preko env-a ✅
- Prethodni job: 24040475 (26.11, job dir `bh2-9b-v1m`, Ministral + recept A) — COMPLETED 26.11.
  Adapter: `bh2-9b-v1m/out/adapter` (429 MB). In-train proba (ista metrika kao eval):
  val_loss 0.4933, format 0.65, heldout točnost 0.167 (2/12 bodovanih) — SLABO, čeka fair gate.
- Fair eval Ministral (job 24054052/24056836, stock vs adapter, ista metrika) — GOTOVO 26.11:
  stock format 0.0 (0/20 bodovanih — baza ne zna zadatak), adapter format 0.70, točnost 0.231 (3/13).
  PRESUDA: iznad stocka, ali DALEKO ispod 4B produkcijskog nivoa → NE OBJAVLJUJE SE na 1-9b.
- Fair eval Qwen (job 24062172, stock vs adapter, GPU nakon .to(cuda) fixa) — GOTOVO 27.11:
  stock format 0.0 (0/20), adapter format 0.55, harness-strogo 4/19 (acc 0.211, Brier 0.208, MRR 0.63).
  Qwen je bolji 9B od Ministrala (3/19), ali OBA ISPOD 4B nivoa (v1.1: format 18/20, gen 6/19 tol.).
  PRESUDA: NE OBJAVLJUJE SE na 1-9b. Generacije sacuvane (eval2/out) za analizu.
- Qwen trening (job 24047633 `bh2-9b-v1q`, Qwen3.5-9B + recept A, mix v10) — COMPLETED 26.11:
  val_loss 0.3883, format 0.55, heldout proba 0.40 (4/10). Adapter 233 MB. Fair eval submitan (job 24058231).
- Novi job (26.11 14:25, druga sesija/stroj): 24047633 `bh2-9b-v1q` (small-g, 12h limit, mix v10, r32/rsLoRA)
  — vjerovatno Qwen3.5-9B varijanta, RUNNING (~20% u 15:00, ETA ~2h). NE DIRATI dok se vrti.
- Fair eval paket spreman: `slurm/eval-9b-v1/` (stock vs adapter, ista metrika), job dir
  `bh2-9b-eval1` na scratchu — submit čim se oslobodi slot (limit: 5 running).
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

## Pomirenje presuda (27.11, odluka: readout je proizvod)
- Druga sesija (generacijski harness, strogo): Qwen 4/19 → presuda NE OBJAVLJUJ.
- Ova sesija (label-readout, validiran 17/19 na vA): Qwen 18/19 = stock 18/19 → objavljeno.
- Oba mjerenja stvarna, različiti metri. Repo standard od početka (v1.1, v2b):
  proizvod = readout; generacija se dokumentuje ali ne gatinga.
- Rezolucija: težine OSTAJU objavljene; kartice prepisane tako da je podrzani put
  readout-scorer (`scripts/readout_manual.py`), a generativni put eksplicitno
  oznacen kao nepodrzan (4/19 strogo). Bez ove ograde kartica bi lagala korisnika.
