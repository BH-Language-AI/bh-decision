# Sheme datasetova BH-Decision (v0.1, protokol v1.0)

Svi izlazi (`reference`) prate protokol v1.0: `decision, options_ranked, scores, risk, confidence, abstention_reason, rationale_short, lang, model, version`.
Seed v0.1 je pilot-skala (5 primjera po datasetu); cilj je min. 1000 primjera po glavnoj kategoriji kad dataset naraste.

| Dataset (fajl) | Zadatak | Ulazna polja | Izlazna polja (`reference`) | Split preporuka (train/val/test) | Zaštita od leakagea |
|---|---|---|---|---|---|
| Choice (`choice.jsonl`) | izbor jedne opcije | `state, options[]` | `decision, options_ranked, scores, risk, confidence, rationale_short` | 70/15/15 | dedup hash (`id`+`state`), embargo test seta |
| Ranking (`ranking.jsonl`) | rangiranje opcija | `state, options[]` | `decision (=top-1), options_ranked, scores, risk, confidence, rationale_short` | 70/15/15 | dedup hash, embargo test seta |
| Scoring (`scoring.jsonl`) | bodovanje svake opcije 0–1 | `state, options[]` | `scores{}, decision, risk, confidence, rationale_short` | 70/15/15 | dedup hash, embargo test seta |
| Risk (`risk.jsonl`) | procjena rizika odluke | `state, options[]` | `risk{level,factors}, decision, confidence, rationale_short` | 70/15/15 | dedup hash, embargo test seta |
| Multicriteria (`multicriteria.jsonl`) | odluka po više kriterija | `state, options[]` | `decision, options_ranked, scores, risk, confidence, rationale_short` | 70/15/15 | dedup hash, embargo test seta |
| Confidence (`confidence.jsonl`) | kalibrirana pouzdanost | `state, options[]` | `confidence, decision, risk, rationale_short` | 70/15/15 | dedup hash, embargo test seta |
| Abstention (`abstention.jsonl`) | suzdržavanje kad fali info | `state, options[]` | `decision="abstain", abstention_reason, confidence (niska), risk` | 60/20/20 | dedup hash, embargo test seta |
| Benchmark (`benchmark.jsonl`) | mješoviti eval uzorak | `state, options[]` | pun protokol v1.0 | ne trenirati — samo eval | strogi embargo, hash + zaključan ref |

Pravila provenancea: svaki red ima `source: "manual-seed-v0.1"`, `license: "CC-BY-4.0"`, ID `BH-D-<ds>-NNN`. Test set je pod embargom — ne ulazi u trening niti u prompt primjere.
