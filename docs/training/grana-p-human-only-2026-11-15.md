# Kontrolni eksperiment: samo-human podaci (2026-11-15, LUMI, job 23766720, 7 min)

> Trening isključivo na 200 ljudski-pisanih stavki (v0.5+v0.6), bez šablona.

## Rezultat

- `val_loss: 0.74`, format_valid_rate **0.35** (raspad formata!), held-out 2/7 parseabilnih (29%).

## Zaključak

- 200 human stavki je premalo da model nauči i format i odluke — format se raspao.
- Šabloni su potrebni za format-stabilnost; human podaci za rasuđivanje. Treba miks s
  većim udjelom human podataka (cilj 500+), ne human-only.
- Sljedeće: još ~300 ljudskih stavki → mix v2 → rerun.
