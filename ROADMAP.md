# BH-Decision — Roadmap

## FAZA 1 — Research & Model Selection ✅ nacrt gotov (2026-11-12), čeka odobrenje
- GH/HF org provjerene (postoje; naziv BH-Decision slobodan).
- Decision poređenje, EU foundation analiza, prijedlog arhitekture, preporuka + pilot.
- Izlazi: `docs/model-selection/decision-model-comparison.md`, `docs/model-selection/european-foundation-models.md`, `docs/architecture/proposed-architecture.md`, `docs/decisions/phase-1-recommendation.md`.

## FAZA 2 — Architecture & Training Design (sljedeće, treba odobrenje)
- Zamrznuti glave, protokol v1.0, plan distilacije, trening plan s VRAM/GPU procjenama.

## FAZA 3 — Dataset & Benchmark
- Sheme 8 datasetova, validacijski primjeri, BH-Decision-Benchmark (min. 1.000 primjera po glavnoj kategoriji), manifesti, leakage zaštita.

## FAZA 4 — Project Infrastructure ✅ kolekcija gotova (2026-11-12)
- HF kolekcija BH-Decision: https://huggingface.co/collections/BH-Language-AI/bh-decision-6af57d53051dc84ba678cb41 (6 referentnih modela FAZE 1; vlastite težine tek nakon validacije u FAZI 7).
- Skripta: `scripts/create_hf_collection.py` (idempotentna, ponovo se pokreće za dodavanje BH-Decision-2B/4B/9B).

## FAZA 5 — Pilot Training
- Mali piloti A vs B vs C, izbor pobjednika dokazom.

## FAZA 6 — Family Training
- 9B, 4B, 2B po pobjedničkoj strategiji, zajednička evaluacija, optimizacija.

## FAZA 7 — Release
- Model cardovi (bs+en), odobrene težine i datasetovi, benchmark, rezultati.

> Pravilo: bez preskakanja faza; bez skupih GPU jobova i bez objava bez plana, licence i odobrenja. Nosioci: Kolektiv d.o.o. + Gamatrade d.o.o.

## Decision Intelligence staza (odvojeno od treninga / separate from training)

> Infrastruktura za odlučivanje (skill + MCP + plugin + core) živi u vlastitim
> paketima i NE mijenja trening configs/scripts/datasets. / Decision infrastructure
> lives in its own packages and does NOT touch training code.

## DI FAZA 1 — Discovery ✅ nacrt gotov (2026-11-12), čeka odobrenje
- Provjereno: Jev 1.13 Free (endpoint, format, cijena, limited-time), Clef-Flash
  (Apache-2.0, SystemOne kompatibilnost, lokalno/hosted opcije), OpenCode plugin API
  v2.2.7, skill format, MCP SDK v1.32.2.
- Korekcija: stvarni tipovi su `noul/choice/score`, ne `categorical/boolean`.
- Izlazi: `docs/architecture/system-architecture.md`, `docs/providers/jev.md`,
  `docs/providers/clef-flash.md`, `docs/decisions/provider-selection.md`.
