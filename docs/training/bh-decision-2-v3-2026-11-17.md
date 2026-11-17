# BH-Decision-2 mix v3 run (2026-11-17, LUMI dev-g MI250X, bf16, job 23816816, 1:11)

> Tacit-4B + LoRA (r16, 3 epohe, bf16) na `train-v3.jsonl` (5189: mix v2 + 200 human-v06).
> Sirovo: `/scratch/.../bh2-mixv3/out/` (adapter + metrike + generacije).

## Rezultat (strogi harness / tolerantni parse)

| Metrika | Strogo | Tolerantno (raw_decode prvog objekta) |
|---|---|---|
| Format validan | 1/20 (0.05) | 20/20 |
| Held-out tačno | 0/1 | **6/19 (32%)** |
| Distribucija | — | o1 4 / o2 9 / o3 7 |
| val_loss | 0.0999 | (memorisanje, bez vrijednosti) |

Poređenje: stock 7/19 (37%) > v3 6/19 (32%) > v1 4/15 > v2 2/10.

## Dijagnoza

1. **v06 je slomio o2-default** (19/20 → 9/20): balansirani human podaci s
   plauzibilnim distraktorima pomiču prior — prvi dokaz da podaci, a ne
   subsample, rješavaju degeneraciju. Smjer tačan, doza mala.
2. **Nova bolest: trailing garbage** — model dodaje višak `}` i halucinirane
   druge objekte (`{"options": {...`) iza validnog JSON-a; strogi parse puca,
   jezgra je ispravna. Plus papagaj metadata (`"model": "human-reference"` —
   polja iz trening targeta cure u izlaz).
3. **Rasuđivanje i dalje ispod stocka** (6/19 vs 7/19, unutar šuma ±2):
   tri SFT runa, tri poraza od netaknutog backbonea. val_loss pada (0.80→0.124→0.0999)
   dok held-out stoji — čista slika memorizacije.

## Zaključak

- **SFT linije se zatvaraju**: v06 je dokazao mehanizam (prior se da pomaknuti),
  ali tri uzastopna poraza od stocka + memorizacija kažu da LoRA-SFT na ovom
  zadatku ne vodi preko 7/19 bez reda veličine više human podataka.
- Put proizvoda ne treba backbone-SFT: DI staza sa sudzuki-4b-cloud daje
  15/18 (83%) na istom held-outu — inferencija, ne trening.
- Preostalo ako se ikad vrati: v07 (još 200+ o3-teških) + stroži target format
  (bez metadata polja) + max_new_tokens veći od 256 da se ne siječe.
