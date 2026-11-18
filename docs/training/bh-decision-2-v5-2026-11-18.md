# BH-Decision-2 mix v5 run (2026-11-18, LUMI dev-g MI250X, bf16, job 23838644)

> Tacit-4B + LoRA (r16, 3 epohe, bf16) na `train-v5.jsonl` (3627: o1=o2=o3=778).
> Odlučujući eksperiment: potpuno balansiran miks, bez prior-izgovora.

## Rezultat

| Metrika | Vrijednost |
|---|---|
| val_loss | 0.1668 (najviši dosad — manje memorizacije) |
| Format (strogi) | 11/20 (0.55) — pad s v4 0.85 |
| Held-out (strogo) | 1/10 (0.10) |
| Held-out (tolerantno) | **3/19 (16%)** |
| Distribucija | o1 4 / o2 7 / o3 9 — bez defaulta |

## Presuda (po unaprijed zapisanom pravilu)

- Bez priora na koji bi se naslonio, model **nagađa na nivou šanse**.
  Balans je uklonio default, a ispod njega nije bilo rasuđivanja.
- Serija kompletna: stock 7/19 (37%) > v3 6/19 > v1 4/15 > v4 3/16 ≈ v5 3/19 > v2 2/10.
  Pet runova, pet poraza od netaknutog backbonea.
- **SFT na šablonima je gotov — točka.** Subsample, čišćenje i balans su
  iscrpili što template-podaci mogu dati: format se da popraviti (0.85),
  prior se da micati (o2→o3→nijedan), ali rasuđivanje se ne pojavljuje.
- Jedini preostali put treninga: red veličine više ljudski-pisanih podataka
  s plauzibilnim distraktorima (timski posao, ne solo autorstvo) — ili ništa.
