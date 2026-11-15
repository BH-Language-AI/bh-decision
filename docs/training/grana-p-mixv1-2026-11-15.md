# Grana P mix-v1 — LUMI bf16 (2026-11-15, job 23764883, 44 min)

> Podaci: train-mix-v1 (4757: v0.3 2378 + v0.4 2248 + v0.5 human 131), held-out v1 (20).
> Model: Ministral-3-3B-Base, LoRA r16, bf16, 3 epohe, 4281/476 split.

## Rezultat

- `val_loss: 0.076`, format 1.0 (20/20), **held-out 5/19 (26%)**.
- Važno: nema više defaulta na jednu labelu (tačni su i o1 i o2) — balans je uklonio
  trivialni prior-exploit. Ostatak jaza je pravi manjak generalizacije, ne artefakt balansa.
- Kaggle QLoRA na istom miksu je u redu čekanja (redundantno — LUMI pobijedio u trci).

## Šta ovo znači (pošteno)

- Template podaci (čak i balansirani) uče formu, ne rasuđivanje: 26% na neviđenom.
- v0.5 human stavki ima samo 131 — premalo da prevagne 4600 šablona.
- Sljedeći korak s najvećom vrijednosti: **skalirati ljudski-pisane podatke** (cilj 500+),
  ili prihvatiti da je 3B LoRA plafon na ~25-50% i preći na Korak 2 (self-distillation).
- Adapter: `/scratch/project_465003647/bh-decision/grana-p-v2/out/adapter` (LUMI scratch, trajno).
