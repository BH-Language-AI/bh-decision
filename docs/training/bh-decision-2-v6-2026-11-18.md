# BH-Decision-2 mix v6 run (2026-11-18, LUMI dev-g MI250X, bf16, 5 epoha, job 23842373)

> Tacit-4B + LoRA na `train-v6.jsonl` (4543, dedup). Zadnji template eksperiment.

## Rezultat (generacijski harness)

| Metrika | Vrijednost |
|---|---|
| val_loss | 0.125 |
| Format (strogi) | **0/20 (0.0)** |
| Held-out | 0/20 (sve nevalidno) |

## Dijagnoza

- 5 epoha na manjem setu = model postao **opširan**: izlazi predugački, svi
  odsječeni na 800 znakova → strogi parse 0/20. Dedup + duži trening pogoršali
  ono što je v4 čišćenje popravilo.
- Konačna readout provjera v6 adaptera je u toku (lokalni CPU); ako ni ona ne
  tuče stock 16/19 → trening se zatvara po pre-registriranom pravilu.

## Readout (2026-11-18, lokalni CPU, q1): 15/19

- v6 adapter kroz joint head: **15/19**, dist o1 14 / o2 5 — identično v4 i v5.
  Sva tri adaptera stoje na 15, stock na 16. Duži trening ne miče readout.
- Konačna serija (readout): stock 16 > v4 = v5 = v6 15.
- **Pravilo izvršeno: trening se zatvara.** Nijedan adapter ne tuče stock;
  razlika je stabilnih 1 item kroz 3 adaptera i 2 pitanja-formulacije.
