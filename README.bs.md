# BH-Decision

Porodica modela za odlučivanje na bosanskoj ijekavici + engleskom: tri veličine (2B/4B/9B), jedan format podataka, zajedničke izlazne sheme, zajednički benchmark. Nosioci: Kolektiv d.o.o. + Gamatrade d.o.o. Kontakt: xnetba@gmail.com.

Ovo je primarni README (ijekavica). Kraća engleska verzija: [README.md](README.md).

## Status (18.11.2026)

- FAZE 1–4 — gotove (istraživanje, arhitektura, dataseti/benchmark, infrastruktura).
- FAZA 5 — Pilot + Linija 2 do **v0.2-rc**: `BH-Language-AI/bh-decision-2-4b`
  (LoRA na Tacit-4B, readout 15/19 naspram stocka 16/19 — [objave](../../releases)).
  SFT na šablonima zatvoren peticom poraza od stocka; nalazi u `docs/training/`.
  Bez daljih GPU poslova bez human 10x.
- DI staza — Core/MCP/Skill/Plugin gotovi (71 test zeleno); sudzuki-4b-cloud
  profilisan (15/18, ECE 0.16); izbor providera čeka cijenu/licencu.
  Vlastiti cjevovod ovdje ne radi bez ključa (Jev mrtav, Clef nema).

## Struktura

```
configs/         trening konfiguracije 2b/4b/9b
scripts/         train.py, evaluate.py (+Brier), build_bh2_mix*.py, readout_eval.py, pilot.py
slurm/ kaggle/  LUMI sbatch + Kaggle kerneli (mix v2–v5, svi runovi)
tests/           24 pytest + 47 TS (core/mcp/plugin/integracija)
docs/            izbor modela, arhitektura, odluke, trening (v1–v5 + readout izvještaji), provideri (jev/clef/sudzuki)
benchmarks/      harness (tačnost + Brier) + izvještaji
datasets/        train-mix-v1/v2, bh-decision-2 (mix v2–v5), expanded-v05..v07 human, heldout-v1 (zaključan)
packages/        decision-core, decision-mcp, opencode-plugin
skills/          decision-intelligence (SKILL.md)
```

## Kako pokrenuti testove

```bash
pip install pytest pyyaml
python3 -m pytest tests/ -q
python3 scripts/train.py --config configs/2b.yaml   # dry-run: samo validira i ispisuje plan
python3 scripts/evaluate.py --ref ref.json --pred pred.json [--out out.json]
```

Pravi trening je zabranjen bez `--confirm` i `BH_DECISION_ALLOW_TRAIN=1` — to je FAZA 5/6 uz odobrenje.

## Licenca

Apache License 2.0 — vidi [LICENSE](LICENSE). Doprinosi: [CONTRIBUTING.md](CONTRIBUTING.md). Upravljanje: [GOVERNANCE.md](GOVERNANCE.md). Sigurnost: [SECURITY.md](SECURITY.md).

## Citiranje

Vidi [CITATION.cff](CITATION.cff).
