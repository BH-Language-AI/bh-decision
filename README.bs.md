<div align="center">

# 🤖 BH-Decision

**Porodica modela za odlučivanje na bosanskoj ijekavici + engleskom**<br>
<i>3 veličine (2B/4B/9B) · jedan format podataka · zajedničke izlazne sheme · zajednički benchmark</i>

[![Licenca](https://img.shields.io/badge/Licenca-Apache--2.0-blue.svg)](LICENSE)
[![Testovi](https://img.shields.io/badge/testovi-24_Py_%2B_47_TS-zeleno-green.svg)](#-testovi)
[![Held-out](https://img.shields.io/badge/heldout_readout-15%2F19-yellowgreen.svg)](https://huggingface.co/datasets/BH-Language-AI/bs-decision-heldout-v01)
[![Model](https://img.shields.io/badge/model-v1.0-yellowgreen.svg)](https://huggingface.co/BH-Language-AI/bh-decision-2-4b)
[![Dataseti](https://img.shields.io/badge/dataseti-21_stavka-blue.svg)](https://huggingface.co/collections/BH-Language-AI/bh-decision-6af57d53051dc84ba678cb41)
[![Benchmark](https://img.shields.io/badge/benchmark-mjereno_ne_obećano-orange.svg)](docs/benchmarking/anyjev-comparison.md)

Nosioci: **Kolektiv d.o.o.** + **Gamatrade d.o.o.** · Kontakt: xnetba@gmail.com<br>
Kraća engleska verzija: [README.md](README.md).

</div>

> ## 🏆 Najbolji rezultati
> | Šta | Skor | Gdje |
> |---|---|---|
> | **Stock Tacit-4B, readout** | **16/19 (84%)** | held-out v1 |
> | **v1.0 (mix v4) + readout, q2/q3** | **16/19 (84%) — paritet** | held-out v1 |
> | v1.0 generacija (tolerantno) | 6/19 (32%) | held-out v1 |
> | Format (strogi JSON) | **18–20/20** (mix v9: 18/20) | held-out v1 |
> | Jev 1.13 Free, DI staza | 14/14 (100%), p50 256 ms | 18 scenarija A/B |
> | Sudzuki-4b-cloud, DI staza | 15/18 (83%) | held-out v1 |
>
> Proizvodna konfiguracija: **v1.0 + AnyJev readout + q2/q3 formulacija** = paritet sa stockom.
> Pravilo repoa: bez fabriciranja — svaka brojka ispod je iz stvarnog runa.

## Status (20.11.2026)

- FAZE 1–4 — gotove (istraživanje, arhitektura, dataseti/benchmark, infrastruktura).
- FAZA 5 — Linija 2 do **v1.0**: [`BH-Language-AI/bh-decision-2-4b`](https://huggingface.co/BH-Language-AI/bh-decision-2-4b)
  (LoRA na Tacit-4B; readout paritet 15–16/19; generacija tolerantno 7/19).
  SFT serija v1–v9: format popravljen podacima (0.05→0.90), prior mican (o2→o3→nijedan),
  rasuđivanje ostalo na stock nivou. Nalazi: [`docs/training/`](docs/training/).
- DI staza — Core/MCP/Skill/Plugin gotovi (**71 test zeleno**); sudzuki-4b-cloud
  profilisan (15/18, ECE 0.16); izbor providera čeka cijenu/licencu.
  Vlastiti cjevovod ovdje ne radi bez ključa (Jev mrtav, Clef nema).

## 📊 Benchmark modela — held-out (20 neviđenih, 19 bodovanih)

![held-out rezultati](docs/heldout-chart.png)

| Verzija | Readout | Generacija (tolerantno) | Generacija (strogo) | val_loss |
|---|---|---|---|---|
| stock Tacit-4B | **16/19 (84%)** | 7/19 (37%) | — | — |
| ✅ v1.0 (mix v4, q2/q3) | **16/19 (84%)** | 6/19 (32%) | 1/20 | 0.100 |
| v0.2-rc (mix v4) | 15/19 (79%) | 6/19 (32%) | 1/20 | 0.100 |
| v0.1 (mix v2) | — | 2/10 (20%) | 10/20 | 0.124 |

Eval set: [bs-decision-heldout-v01](https://huggingface.co/datasets/BH-Language-AI/bs-decision-heldout-v01) (zaključan, leakage 0).
Slike/grafike: bedževi su shields.io, graf je mjereni held-out (matplotlib, sirovi brojevi iznad).

<details>
<summary>📈 Decision Intelligence benchmark (18 scenarija, 9 bs + 9 en) — klikni za detalje</summary>

| Ruta | Tačnost (12.11.) | Rerun (13.11.) | p50 rerun | Reproducibilnost |
|---|---|---|---|---|
| A Jev-1.13-Free (hosted, $0) | 14/14 (100%) | **14/14** | 256 ms | bit-za-bit ✓ |
| B AnyJev Decider L0 (Tacit-4B, CPU) | 11/14 (79%) | **11/14** strogo | 17,1 s | 18/18 identično ✓ |
| C AnyJev Tacit L0 (CPU) | 11/14 norm. | **9/14** strogo (= 11 norm.) | 6,4 s | 18/18 identično ✓ |
| D Tacit Adaptive | 11/14 | nije ponavljan (D==C dokazano, cot 0/18) | — | — |
| E Clef lokalno | — | blokirano (treba GPU/download) | — | — |

Sirovo: `benchmarks/reports/live-{A-jev,B-decider-l0,C-tacit-l0,D-tacit-adaptive}.json`
+ `*-rerun-20261113.json`. Metodologija: `docs/benchmarking/anyjev-comparison.md`.

Agent sa skillom je brži i bolji: L0 je jedan forward (CPU) ili jedan hosted poziv (p50 256 ms);
svaka odluka nosi kalibrirano povjerenje; ispod praga 0.80 slijedi eskalacija.
Tok: zadatak → determinističko pravilo? → L0 → confidence ≥ 0.80? → izvrši, inače eskalacija.

</details>

## ✅ Testovi

| Sloj | Broj | Komanda |
|---|---|---|
| Python (pytest) | **24 zeleno** | `python3 -m pytest tests/ -q` |
| TypeScript (core/mcp/plugin/integracija) | **47 zeleno** | `node --experimental-strip-types --test tests/core/normalize.test.ts tests/core/providers.test.ts tests/core/anyjev.test.ts tests/mcp/server.test.ts tests/plugin/loading.test.ts tests/integration/project.test.ts` |

```bash
pip install pytest pyyaml
python3 -m pytest tests/ -q
python3 scripts/train.py --config configs/2b.yaml   # dry-run: samo validira i ispisuje plan
python3 scripts/evaluate.py --ref ref.json --pred pred.json [--out out.json]  # +Brier scoring
```

## 📁 Struktura

```
configs/         trening konfiguracije 2b/4b/9b
scripts/         train.py, evaluate.py (+Brier), build_bh2_mix*.py, readout_eval.py, readout_qsweep.py, readout_v*.py, pilot.py
slurm/ kaggle/  LUMI sbatch + Kaggle kerneli (mix v2–v9, svi runovi)
tests/           24 pytest + 47 TS (core/mcp/plugin/integracija)
docs/            izbor modela, arhitektura, odluke, trening (v1–v9 + readout izvještaji), provideri (jev/clef/sudzuki)
benchmarks/      harness (tačnost + Brier) + izvještaji
datasets/        train-mix-v1/v2, bh-decision-2 (mix v2–v9), expanded-v05..v09 human, heldout-v1 (zaključan), external (CSQA+QASC+ETHICS)
packages/        decision-core, decision-mcp, opencode-plugin
skills/          decision-intelligence (SKILL.md)
```

## Decision Intelligence staza (odvojeno od treninga)

Skill + MCP server + OpenCode plugin + zajednički Core. Ne mijenja trening kod: `packages/`, `skills/`, `config/`.

- Arhitektura: `docs/architecture/system-architecture.md`, `docs/architecture/decision-protocol.md`
- Provideri: `docs/providers/jev.md`, `docs/providers/clef-flash.md`, `docs/providers/sudzuki.md`, `docs/decisions/provider-selection.md`
- Instalacija: `docs/installation/opencode.md`, `docs/installation/local-clef.md`
- Verzije: basic (Jev Free) vs advanced (lokalni Tacit-4B) — `docs/installation/tiers.md`
- Privatnost: `docs/security/privacy.md` — Benchmark: `benchmarks/reports/phase-6.md`

## Licenca

Apache License 2.0 — vidi [LICENSE](LICENSE). Doprinosi: [CONTRIBUTING.md](CONTRIBUTING.md). Upravljanje: [GOVERNANCE.md](GOVERNANCE.md). Sigurnost: [SECURITY.md](SECURITY.md).

## Citiranje

Vidi [CITATION.cff](CITATION.cff).
