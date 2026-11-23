# BH-Decision-2 mix v8 run (2026-11-19/20, LUMI dev-g MI250X, bf16, job 23866674)

> Tacit-4B + LoRA (r16, 3 epohe, bf16) na `train-v8.jsonl` (7529: mix v7 + 1k CSQA + 1k ETHICS).
> Prvi test eksternog EN-a.

## Rezultat (generacijski harness)

| Metrika | Vrijednost |
|---|---|
| val_loss | 0.357 (najviši — eksterno se teže memoriše) |
| Format (strogi) | 14/20 (0.70) |
| Held-out (tolerantno) | **5/19 (26%)**, dist o3 13 / o1 4 / o2 2 |

## Dijagnoza

- Eksterna doza NIJE pomogla: 5/19 < v7 7/19. Prior se opet pomaknuo (sad o3 13/20)
  umjesto da se pojavilo rasuđivanje. val_loss raste (manje memorizacije) ali
  held-out ne prati — EN trivia ne transferira na bs odluke.
- Po pravilu: eksterno se NE širi dalje. Ostaje readout provjera v8 adaptera
  (ako da ≥16/19, v8 postaje kandidat; inače se gasi i ova grana).

## Readout: BLOKIRAN (cert)

- v8 adapter na scratchu, skidanje ne ide — EFP cert istekao i na Oracle skočnom čvoru.
- Čim se cert osvježi: merge + readout (očekivanje po obrascu: 15/19).

## Readout (2026-11-23, lokalni CPU, q1): 17/19

- Identični promašaji kao v1.1 (013 gibberish, 016 najteža stavka).
- v8 potvrđuje 17/19 kao reproducible nivo, ali generacija mu je gora (5/19 vs 6/19)
  pa nema nove objave — v1.1 ostaje final.
