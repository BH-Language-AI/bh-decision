# BH-Decision — Roadmap

## FAZA 1 — Research & Model Selection ✅ nacrt gotov (2026-11-12), čeka odobrenje
- GH/HF org provjerene (postoje; naziv BH-Decision slobodan).
- Decision poređenje, EU foundation analiza, prijedlog arhitekture, preporuka + pilot.
- Izlazi: `docs/model-selection/decision-model-comparison.md`, `docs/model-selection/european-foundation-models.md`, `docs/architecture/proposed-architecture.md`, `docs/decisions/phase-1-recommendation.md`.

## FAZA 2 — Architecture & Training Design (sljedeće, treba odobrenje)
- Zamrznuti glave, protokol v1.0, plan distilacije, trening plan s VRAM/GPU procjenama.

## FAZA 3 — Dataset & Benchmark
- Sheme 8 datasetova, validacijski primjeri, BH-Decision-Benchmark (min. 1.000 primjera po glavnoj kategoriji), manifesti, leakage zaštita.

## FAZA 4 — Project Infrastructure ✅ gotova (2026-11-12)
- GH repo (sadržajan, ne prazan): https://github.com/BH-Language-AI/bh-decision — 19 testova zeleno, CI, seed datasetovi (40 primjera), benchmark harness verificiran end-to-end.
- HF kolekcija BH-Decision: https://huggingface.co/collections/BH-Language-AI/bh-decision-6af57d53051dc84ba678cb41 (6 referentnih modela FAZE 1; vlastite težine tek nakon validacije u FAZI 7).

## FAZA 5 — Pilot Training ✅ smoke + pravi pilot B (2026-11-12, Kaggle T4)
- Dokaz pipelinea: EuroLLM-1.7B + LoRA, loss 1.725→0.025 (100 koraka), izlaz validan protokolski JSON na ijekavici. Izvještaj: `docs/training/pilot-b-smoke-2026-11-12.md`.
- Pravi pilot B: val_loss 0.491 (360/40, 3 epohe), format_valid_rate 0.4 — limit probe bio odsijecanje na 128 tokena (sljedeći run: 256). Izvještaj: `docs/training/pilot-b-2026-11-12.md`.
- Adapteri neobjavljeni. Preostalo: ljudska validacija uzorka, krak C + clef-flash baseline na ≥24GB GPU-u.
- Mali piloti A vs B vs C po `docs/training/pilot-faza5.md`, izbor pobjednika dokazom (`scripts/pilot.py`, `slurm/pilot.slurm`).

## FAZA 6 — Family Training
- 9B, 4B, 2B po pobjedničkoj strategiji, zajednička evaluacija, optimizacija.

## FAZA 7 — Release
- Model cardovi (bs+en), odobrene težine i datasetovi, benchmark, rezultati.

> Pravilo: bez preskakanja faza; bez skupih GPU jobova i bez objava bez plana, licence i odobrenja. Nosioci: Kolektiv d.o.o. + Gamatrade d.o.o.

## Decision Intelligence staza (odvojeno od treninga / separate from training)

> Infrastruktura za odlučivanje (skill + MCP + plugin + core) živi u vlastitim
> paketima i NE mijenja trening configs/scripts/datasets. / Decision infrastructure
> lives in its own packages and does NOT touch training code.

## DI FAZA 1 — Discovery ✅ gotovo (2026-11-12)
- Provjereno: Jev 1.13 Free (endpoint, format, cijena, limited-time), Clef-Flash
  (Apache-2.0, SystemOne kompatibilnost, lokalno/hosted opcije), OpenCode plugin API
  v2.2.7, skill format, MCP SDK v1.32.2.
- Korekcija: stvarni tipovi su `noul/choice/score`, ne `categorical/boolean`.
- Izlazi: `docs/architecture/system-architecture.md`, `docs/providers/jev.md`,
  `docs/providers/clef-flash.md`, `docs/decisions/provider-selection.md`.

## DI FAZE 2–6 — Core/MCP/Skill/Plugin/Benchmark ✅ gotovo (2026-11-12)
- Core, 14 MCP alata (11 + 3 anyjev), skill (+AnyJev sekcija), plugin (`/decision`, `/decision-status`, `provider=` prefiks), 43 TS + 19 Python testova zeleno.
- Ispravljena 2 bug-a pronađena testiranjem (breaker reset, redactSecrets).
- AnyJev adapter (tacit/decider, l0/adaptive, bridge+gateway) — default off, mock-testiran; live mjerenja blokirana (nema modela/ključa, nisu fabricirana).
- Izvještaj: `benchmarks/reports/phase-6.md`. Odluka: `docs/decisions/anyjev-integration.md`.

## DI FAZA 7 — Release priprema (sljedeće, treba odobrenje)
- [ ] `git init` + prvi commit (BH-Decision još nije git repo, nema remotea)
- [ ] Instalacijska provjera na čistom checkoutu (skill load, MCP handshake, plugin load u OpenCode)
- [ ] Live benchmark uz korisnički `OPENCODE_API_KEY` i/ili lokalni Clef (uz odobrenje downloada)
- [ ] GitHub repo + release — SAMO uz eksplicitno odobrenje
