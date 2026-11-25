# BH-Decision-2 recept A (r32/rsLoRA/cosine/1024, 4 epohe, mix v10) — LUMI job 23962923

## Recept (prijedlog istraživačkog tima, usvojen)

- LoRA r=32, alpha=64, dropout=0.05, **rsLoRA**, targeti q/k/v/o/gate/up/down
- lr 1e-4, cosine scheduler, warmup 10% (~pocetnih koraka), eff. batch 32, max_len 1024
- Implementacija: `slurm/grana-p-v2/train_grana_p.py` (sve preko env varijabli, backward compatible)

## Rezultat (generacijski harness)

| Metrika | Vrijednost |
|---|---|
| val_loss | 0.432 |
| Format (strogi) | 4/20 (0.20) |
| Held-out (tolerantno) | 5/19 (26%), dist o3 14 — o3-default se vratio |

Generacija i dalje slaba — ali to više nije mjerilo proizvoda.

## Readout (lokalni CPU, q1): 18/19 (95%)

- Jedini promašaj: 013 gibberish (choice ne može apstinirati — strukturno).
- Na svim odlučivim stavkama: **18/18 (100%)**.
- Kalibracija: Brier **0.033** (najbolji), ECE **0.105** (najbolji).
- Poređenje readout q1: stock 16, v4/v5/v6/v7 15, v9 17, **vA 18**.

## Readout q2/q3 (lokalni CPU, 2026-11-24, logovi `readout-vAq23.log`)

- q2: **16/19** (promašaji 011, 013, 016) — acc 0.842, Brier 0.099, ECE 0.155.
- q3: **18/19** (promašaj samo 013 gibberish) — acc 0.947, Brier 0.053, ECE 0.082.
- Ukupno sve formulacije: q1 18/19, q2 16/19, q3 18/19 — vodstvo robustno,
  jedini dosljedni promašaj je strukturni 013 (choice bez apstinencije).
- Sirovo: `datasets/selfdistill/readout-vA.jsonl` (q1),
  `datasets/selfdistill/readout-vAq23.jsonl` (q2+q3).

## Zaključak

- Novi recept radi: veći rank + rsLoRA + cosine + duži kontekst = disciplinovaniji readout.
- Generacijski interfejs i dalje varira (5/19) — proizvod ostaje readout.
- **v0.5-rc: vA adapter, 18/19.** Prvi model koji na svim odlučivim stavkama ne griješi.
