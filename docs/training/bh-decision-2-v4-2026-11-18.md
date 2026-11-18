# BH-Decision-2 mix v4 run (2026-11-18, LUMI dev-g MI250X, bf16, job 23836300)

> Tacit-4B + LoRA (r16, 3 epohe, bf16) na `train-v4.jsonl` (5389: mix v3 + 200 human-v07,
> targeti očišćeni na 7 ključeva). Sirovo: `/scratch/.../bh2-mixv4/out/`.

## Rezultat

| Metrika | Vrijednost |
|---|---|
| val_loss | 0.1229 |
| Format (strogi) | **17/20 (0.85)** — čišćenje radi |
| Held-out tačno | **3/16 (19%)** — pad |
| Distribucija | o1 3 / o2 5 / o3 9 (+3 nevalidna) |

Poređenje: stock 7/19 (37%) > v3 6/19 > v1 4/15 > v4 3/16 > v2 2/10.

## Dijagnoza

1. **Čišćenje targeta radi**: format 0.05 → 0.85, trailing garbage nestao,
   papagaj metadata nestao. Format-problem riješen podacima, ne kodom.
2. **Klatno se prebacilo**: o2-default (19/20) → o3-lean (9/17). Dva o3-teška
   human seta (v06+v07, o3 100/200 svaki) nadjačala su šablone. Prior se da
   upravljati — ali upravljanje priorom nije rasuđivanje.
3. **Held-out je o1-težak** (većina referenci o1); model koji defaulta o3 pada.
   Gađanje 20-item seta pomicanjem priora je overfitting na quirks seta, ne učenje.
4. Strukturni korijen: šabloni su o1/o2-teški (1659/1659) uz o3 778 — nijedan
   ljudski dodatak od 200 to ne balansira; treba ili rezanje ili 900+ o3 stavki.

## Sljedeće (mix v5 — odlučujući eksperiment)

- Subsample o1/o2 šablona na nivo o3 (~778): potpuno balansiran miks (~3500).
  Ako balansiran model pokaže rasuđivanje (blizu stocka bez defaulta) → skaliranje
  podataka ima smisla. Ako padne na chance → SFT na šablonima je mrtav, točka.
