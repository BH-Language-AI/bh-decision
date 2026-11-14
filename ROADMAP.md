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

## FAZA 5b — BH-Decision-4B grana (novo, 2026-11-13, dvije eksperimentalne grane)

- **Grana R (referentna, gotova): Tacit-4B-Benchmark** — originalni `morriszjm/Tacit-4B`
  (dodan u HF kolekciju kao referenca, težine se ne re-uploadaju), samo mjerenja:
  CPU+GPU bench (B/C/D 11/14). Qwen3-4B baza → nikad temelj produkcijskog modela.
- **Grana P (produkcijska): BH-Decision-4B na evropskoj bazi** — metodologija Tacit/AnyJev
  (L0 readout, joint-head paradigma, self-distillation), NE Qwen težine:
  - **Korak 1 — Bosanska specijalizacija (prvo):** vlastiti dataset (ijekavica;
    klasifikacija, rizik, rangiranje, višekriterijsko, pravno/administrativno),
    trening na EU bazi. Kandidati baze za provjeru licence/pogodnosti:
    EuroLLM linija, Ministral, SmolLM — odluka dokazom, ne unaprijed.
    ✅ Prvi dokaz 2026-11-13: Ministral-3-3B-Base + QLoRA na expanded 400 (Kaggle T4):
    val 0.804, format 1.0 — pipeline radi; rationale šablonski → treba veći dataset.
    Izvještaj: `docs/training/grana-p-ministral-pilot-2026-11-13.md`.
    ✅ Drugi dokaz 2026-11-14: expanded-v2 (2378) + held-out v1 (20 neviđenih):
    val 0.163, format 1.0, held-out 10/19 (53%) — model defaulta na o1 (class-imbalance).
    Sljedeće: balansirani dataset v0.4.
    Izvještaj: `docs/training/grana-p-v2-2026-11-14.md`.
  - **Korak 2 — Self-distillation:** model generiše vlastite probleme, rješava uz
    reasoning, uči jedan-prolaz odluke (AnyJev princip, bez tuđih izlaza).
  - **Korak 3 — ⛔ ODBAČENO: Jev distilacija (Faza A)** — odluka korisnika 2026-11-13:
    MCA TypeSafe §2.3(b) zabranjuje distillation/imitation; ne izvoditi.
    Put je B → C, bez tuđih izlaza.
- Kalibracija vjerovatnoća je obavezan cilj treninga i evaluacije (poseban prag + ECE metrika).

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
- AnyJev adapter (tacit/decider, l0/adaptive, bridge+gateway) — default off. Live mjerenja 2026-11-12:
  B Decider L0 11/14, C Tacit L0 11/14, D Adaptive 11/14 (cot 0/18), A Jev Free 14/14 (p50 334 ms);
  E Clef local blokiran (GPU/download). Detalji: `docs/benchmarking/anyjev-comparison.md`.
- Izvještaj: `benchmarks/reports/phase-6.md`. Odluka: `docs/decisions/anyjev-integration.md`.

## DI FAZA 7 — Release priprema (u toku)
- [x] Git repo postoji (`origin`: `BH-Language-AI/bh-decision`, grana `main`) — stavka "git init" iz ranijeg plana je zastarjela.
- [x] Instalacijska provjera na čistom checkoutu (2026-11-13): `git worktree` na HEAD + `npm install` u `decision-mcp` i `opencode-plugin` + puni suite zelen (45 TS + 19 Python); `decision-core` bez zavisnosti.
- [x] Live benchmark + reproducibility reruni (2026-11-13, novi korisnički ključ):
  A 14/14, B 11/14 strogo, C 9/14 strogo — sve bit-za-bit kao 2026-11-12;
  D se ne ponavlja (D==C dokazano, cot 0/18). Sirovi JSON lokalno (gitignore).
- [ ] GitHub push + release — SAMO uz eksplicitno odobrenje (lokalni commitovi se ne pushaju sami)
