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

## Mix v2 (2026-11-16, spreman — čeka GPU odobrenje)

- `scripts/build_bh2_mixv2.py` (seed 7): od v1 miksa (8474) van 3300 ne-JSON
  zapisa (1300 think-tragova + 2000 bosnian-core spama — provjereno travel/ISO
  ekavski boilerplate, nula decision sadržaja), o2 subsample 1744→1559 (= o1).
  Izlaz: `datasets/bh-decision-2/train-v2.jsonl` (4989, samo JSON ciljevi) +
  `manifest-v2.json`. Sljedeće: LoRA run + readout provjera, SAMO uz odobrenje.

## Korak-2 proba v2 (2026-11-16, gotova)

- Popravljen dizajn: 12 novih situacija sa state-specific opcijama
  (`scripts/selfdistill_probe_v2.py`, sirovo `datasets/selfdistill/probe-v2.jsonl`).
- Rezultat: **12/12 pogodak, ali cot=0/12, confidence ~0.99** — distraktori su
  apsurdni (npr. "ostaviti ključ pod otiračem"), pa model bira razumnu opciju
  po površinskoj formi, bez reasoninga. Test je prelagan: ne dokazuje da model
  može generisati vlastite trening podatke, samo da razlikuje razumno od
  apsurdnog. Degenerisani confidence (sve ~1.0) je isti fenomen kao kod Jev-a.
- Napomena o pristrasnosti: autor proba i referentnih odgovora je eksperimentator
  (ista ograda kao A/B v6 Muse grana) — gornja granica, ne nezavisna mjera.
- Pravi Korak-2 test traži uvjerljive distraktore (heldout-stil, sve opcije
  plauzibilne) = isti autorski posao kao human podaci. Pauzirano dok human
  pool ne naraste; v2 ostaje kao negativna kontrola dizajna probi.
