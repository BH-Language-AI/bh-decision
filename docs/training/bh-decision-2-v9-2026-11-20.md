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
