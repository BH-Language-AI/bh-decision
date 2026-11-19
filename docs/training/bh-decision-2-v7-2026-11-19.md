# BH-Decision-2 mix v7 run (2026-11-18/19, LUMI dev-g MI250X, bf16, job 23848999)

> Tacit-4B + LoRA (r16, 3 epohe, bf16) na `train-v7.jsonl` (5529: mix v4 + v08 full
> s rationale_full). Prvi run s reasoning tragovima.

## Rezultat (generacijski harness)

| Metrika | Vrijednost |
|---|---|
| val_loss | 0.158 |
| Format (strogi) | 3/20 (0.15) |
| Held-out (strogo) | 1/3 |
| Held-out (tolerantno) | **7/19 (37%)** — izjednačen stock |

## Dijagnoza

- Tolerantno 7/19 = najbolji generacijski skor ikad (paritet sa stock generacijom).
  Reasoning tragovi nisu odmagli; strogi format i dalje mrtav (kratki odsječak + verbose).
- Readout provjera v7 adaptera BLOKIRANA: EFP cert na Oracle skočnom čvoru istekao
  (isti portal-refresh kao i lokalni). Čeka se osvježenje za merge + readout.
- Ako readout potvrdi ≥16/19 → v0.3-rc kandidat. Ako ostane 15 → paritet, bez prednosti.

## Readout (2026-11-19, lokalni CPU)

|  | q1 | q2 |
|---|---|---|
| v7 | 15/19 | 15/19 |
| stock (referenca) | 16/19 | 13/19 |

v4 ostaje najbolji adapter (16/19 uz q2/q3). Nijedan adapter nigdje ne tuče stock.
Serija readouta: stock 16 ≥ v4 = v5 = v6 = v7 15.
**Trening zatvoren definitivno.** Proizvod = v0.2-rc (v4 adapter) + readout + q2/q3.
