# BH-Decision

Porodica modela za odlučivanje na bosanskoj ijekavici + engleskom: tri veličine (2B/4B/9B), jedan format podataka, zajedničke izlazne sheme, zajednički benchmark. Nosioci: Kolektiv d.o.o. + Gamatrade d.o.o. Kontakt: xnetba@gmail.com.

Primarni README na ijekavici: [README.bs.md](README.bs.md).

## Status (FAZA 1–4)

- FAZA 1 — Research & model selection: nacrt gotov, čeka odobrenje.
- FAZA 2 — Arhitektura i trening dizajn: sljedeća, treba odobrenje.
- FAZA 3 — Dataseti i benchmark: planirano.
- FAZA 4 — Infrastruktura (ovaj repo): u izradi — configi, skripte, CI testovi.
- FAZE 5–7 — Pilot trening, porodični trening, release: nisu počele. Bez GPU jobova i bez objava bez plana, licence i odobrenja.

## Struktura

```
configs/         trening konfiguracije 2b/4b/9b (infrastruktura; trening je FAZA 5/6)
scripts/         train.py (dry-run stub), evaluate.py (omotač oko harness-a)
tests/           pytest: protokol, dataseti, configi (samo stdlib + pytest)
docs/            model-selection, architecture, decisions (FAZA 1)
benchmarks/      harness (FAZA 3, još ne postoji)
datasets/        uzorci (FAZA 3, još ne postoje)
```

## Kako pokrenuti testove

```bash
pip install pytest pyyaml
python3 -m pytest tests/ -q
python3 scripts/train.py --config configs/2b.yaml   # dry-run: samo validira i ispisuje plan
python3 scripts/evaluate.py --ref ref.json --pred pred.json [--out out.json]
```

## Decision Intelligence staza (odvojeno od treninga)

Skill + MCP server + OpenCode plugin + zajednički Core (Jev 1.13 Free → lokalni
Clef-Flash, nulti trošak). Ne mijenja trening kod: `packages/`, `skills/`, `config/`.

- Arhitektura: `docs/architecture/system-architecture.md`, `docs/architecture/decision-protocol.md`
- Provideri: `docs/providers/jev.md`, `docs/providers/clef-flash.md`, `docs/providers/anyjev.md`, `docs/decisions/provider-selection.md`, `docs/decisions/anyjev-integration.md`
- Instalacija: `docs/installation/opencode.md`, `docs/installation/local-clef.md`
- Privatnost: `docs/security/privacy.md` — Benchmark: `benchmarks/reports/phase-6.md`

Testovi (bez ključeva/mreže): `node --experimental-strip-types --test tests/core/normalize.test.ts tests/core/providers.test.ts tests/core/anyjev.test.ts tests/mcp/server.test.ts tests/plugin/loading.test.ts tests/integration/project.test.ts`

## Licenca

Apache License 2.0 — vidi [LICENSE](LICENSE). Doprinosi: [CONTRIBUTING.md](CONTRIBUTING.md). Upravljanje: [GOVERNANCE.md](GOVERNANCE.md). Sigurnost: [SECURITY.md](SECURITY.md).

## Citiranje

Vidi [CITATION.cff](CITATION.cff).
