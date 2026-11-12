# BH-Decision-Benchmark (v0.1, seed/pilot-skala)

Seed v0.1 je pilot-skala (5 primjera u `benchmark.jsonl`); cilj je min. 1000 primjera po glavnoj kategoriji kad dataset naraste.

## 12 obaveznih kategorija (iz FAZE 1: pilot zadaci + baselineovi + robustness)

1. choice — tačan izbor jedne opcije
2. yes_no_constraint — binarni constraint check (blokira odluku)
3. ranking — kvalitet redoslijeda opcija
4. scoring — greška bodovanja opcija
5. risk — tačnost nivoa rizika i faktora
6. multicriteria — odluka po ponderisanim kriterijima
7. confidence — kalibracija pouzdanosti
8. abstention — kvalitet suzdržavanja
9. robustness_paraphrase — stabilnost na parafraze pitanja
10. robustness_order — stabilnost na redoslijed opcija
11. crosslingual_consistency — konzistentnost bs↔en na paralelnim primjerima
12. register_coverage — pokrivenost registara (admin/poslovni/svakodnevni) na ijekavici

## Metrike po kategoriji

| Kategorija | Metrike |
|---|---|
| choice, yes_no_constraint, multicriteria | accuracy |
| ranking | nDCG@k, MRR |
| scoring | MAE |
| risk | accuracy (nivo) |
| confidence | Brier, ECE (10 binova) |
| abstention | precision, recall (abstain = pozitivna klasa) |
| robustness_paraphrase, robustness_order | robustness delta (pad accuracy vs baza) |
| crosslingual_consistency | udio slaganja bs↔en odluka |
| register_coverage | accuracy po registru |

## Pravilo prikaza

Rezultati se prikazuju po jeziku (bs/en) i po zadatku/kategoriji — nikad jedna agregatna ocjena. Bosanski-ijekavski dio je primarni; engleski ne smije degradirati.
