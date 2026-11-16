# BH-Decision-2 (Tacit linija) — baseline i plan (2026-11-16)

> Linije po odluci korisnika: bh-decision-1 = EU/Ministral, bh-decision-2 = Tacit-4B.
> Tacit težine Apache-2.0 (Qwen3 baza — eksperimentalna linija, ne temelj BH-Decision).

## Baseline (mjereno, lokalni CPU)

- Stock `morriszjm/Tacit-4B`, transformers, float32, one_forward: **held-out 7/19 (37%)**,
  0 grešaka, p50 ~7 s. Metar za "prije".
- Naš najbolji Ministral SFT: 5/19 (26%). Tacit stock je trenutno najbolji lokalni rezultat.

## Trening plan (bh-decision-2)

- Baza: Tacit-4B backbone kao causal LM (config kaže Qwen3 arhitektura — radi na LUMI
  transformers 5.19 bez upgradea; joint head se ne dira).
- Podaci: `datasets/bh-decision-2/train.jsonl` (8474: naši šabloni format-sidro +
  200 human + thinking 500 + confirmation 800 + bosnian-core uzorak 2000).
- Cilj: popraviti held-out iznad 7/19 uz očuvan format 1.0; joint head evaluacija naknadno.
- Rizik (iskreno): SFT backbonea može pokvariti joint head readout — provjeriti nakon treninga
  AnyJev readoutom na istoj held-out listi.
