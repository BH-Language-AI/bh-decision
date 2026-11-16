# LUMI mix + 274 human (2026-11-16, job 23780660, 45 min)

> Podaci: train-mix-v1 (4900: v0.3 + v0.4 + 274 human), held-out v1 (20).

## Rezultat

- `val_loss: 0.079`, format 1.0, **held-out 5/19 (26%)** — identično runu bez novih 74 stavki.

## Zaključak

- +74 human stavke (200→274): nula pomaka. Skaliranje ljudskih podataka u stotinama
  ne pomiče iglu — ili treba 10× više, ili je LoRA-SFT na ovom zadatku zasićen.
- Svi SFT runovi: 3/19–11/19 (šum + prior-efekti). Format je riješen (1.0), rasuđivanje nije.
- Preporuka: pauzirati SFT skaliranje. Opcije: (a) masovniji human dataset uz pomoć tima,
  (b) Korak 2 self-distillation prototip, (c) veći/drugačiji base model.
