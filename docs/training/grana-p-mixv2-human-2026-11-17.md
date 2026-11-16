# Mix v2 + 274 human, Kaggle QLoRA (2026-11-17, kernel v7)

> Prvi run na kompletnom miksu (4900: 4626 šablona + 274 human). n_train 4410.

## Rezultat

- `val_loss: 0.183` (teži miks), format 1.0, **held-out 4/19 (21%)**.

## Zaključak serije

| Run | Podaci | val | held-out |
|---|---|---|---|
| pilot Kaggle | 400 šablona | 0.80 | — |
| v2 Kaggle | 2378 šablona | 0.163 | 10/19 (53%) |
| v2-rerun Kaggle | isto | 0.149 | 6/19 (32%) |
| mix-v1 LUMI bf16 | 4626 balansirano | 0.076 | 5/19 (26%) |
| mix+human Kaggle | 4900 (+274 human) | 0.183 | 4/19 (21%) |

- Human udio (5.6%) premali da prevagne; balans ne rješava generalizaciju.
- SFT plafon na ovom zadatku/podacima: ~20-30% held-out, format 1.0.
- SFT skaliranje se pauzira. Sljedeće: (a) human 10×, (b) Korak-2 self-distillation prototip (lokalno, CPU), (c) prihvatiti 5/19 kao baseline i fokus na DI inferenciju.
