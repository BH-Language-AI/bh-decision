# BH-Decision

Porodica modela za odlučivanje na bosanskoj ijekavici + engleskom: tri veličine (2B/4B/9B), jedan format podataka, zajedničke izlazne sheme, zajednički benchmark. Nosioci: Kolektiv d.o.o. + Gamatrade d.o.o. Kontakt: xnetba@gmail.com.

Ovo je primarni README (ijekavica). Kraća engleska verzija: [README.md](README.md).

## Status (FAZA 1–4)

- FAZA 1 — Istraživanje i izbor modela: nacrt gotov, čeka odobrenje.
- FAZA 2 — Arhitektura i dizajn treninga: sljedeća, treba odobrenje.
- FAZA 3 — Dataseti i benchmark: planirano.
- FAZA 4 — Infrastruktura (ovaj repo): u izradi — konfiguracije, skripte, CI testovi.
- FAZE 5–7 — Pilot trening, porodični trening, objava: nisu počele. Bez skupih GPU poslova i bez objava bez plana, licence i odobrenja.

## Struktura

```
configs/         trening konfiguracije 2b/4b/9b (infrastruktura; trening je FAZA 5/6)
scripts/         train.py (dry-run stub), evaluate.py (omotač oko harness-a)
tests/           pytest: protokol, dataseti, konfiguracije (samo stdlib + pytest)
docs/            izbor modela, arhitektura, odluke (FAZA 1)
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

Pravi trening je zabranjen bez `--confirm` i `BH_DECISION_ALLOW_TRAIN=1` — to je FAZA 5/6 uz odobrenje.

## Licenca

Apache License 2.0 — vidi [LICENSE](LICENSE). Doprinosi: [CONTRIBUTING.md](CONTRIBUTING.md). Upravljanje: [GOVERNANCE.md](GOVERNANCE.md). Sigurnost: [SECURITY.md](SECURITY.md).

## Citiranje

Vidi [CITATION.cff](CITATION.cff).
