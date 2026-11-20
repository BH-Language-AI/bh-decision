# BH-Decision-2 mix v9 run (2026-11-20, LUMI dev-g MI250X, bf16, job 23881089)

> Tacit-4B + LoRA (r16, 3 epohe, bf16) na `train-v9.jsonl` (7729: mix v8 + v09 full).
> Test: da li reasoning tragovi + eksterna doza pomiču held-out.

## Rezultat (generacijski harness)

| Metrika | Vrijednost |
|---|---|
| val_loss | 0.413 (najviši — najteži miks) |
| Format (strogi) | **18/20 (0.90)** — najbolji ikad |
| Held-out (strogo) | 5/17 |
| Held-out (tolerantno) | **6/19 (32%)** = v3 nivo, ispod stocka 7/19 |
| Distribucija | o1 8 / o3 6 / o2 4 + abstain/yes (nema defaulta) |

## Dijagnoza

- Eksterna doza + reasoning: format skočio (0.55→0.90), prior raspršen bez
  defaulta — ali tačnost stoji (6/19 = v3). Proces-podaci popravljaju
  disciplinu izlaza, ne i rasuđivanje iznad stocka.
- Readout provjera v9 adaptera odlučuje: ≥16/19 → v0.4-rc; inače kraj.

## Readout (2026-11-20, lokalni CPU, q1): 17/19 (89%)

- Jedini promašaji: 013 (gibberish→abstain, choice ne može apstinirati — strukturno)
  i 016 (najteža stavka, svi modeli griješe).
- **Prvi put iznad stocka (16/19).** Pravilo izvršeno: v9 postaje kandidat za v0.4-rc.

## Kalibracija (q1, n=19)

| Model | Tačnost | Brier ↓ | ECE |
|---|---|---|---|
| stock | 0.84 | 0.048 | 0.124 |
| v4 | 0.79 | 0.042 | 0.154 |
| v5 | 0.79 | **0.022** | 0.159 |
| v9 | **0.89** | 0.048 | 0.186 |

v9: najbolja tačnost, najgori ECE (pre-samouvjeren kad griješi).
v5: najbolji Brier (oprezan). Kalibracijski prag 0.80 iz skill-a i dalje važi —
posebno za v9.
