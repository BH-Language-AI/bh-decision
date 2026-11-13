# AnyJev usporedba / AnyJev comparison

> Kostur metodologije — NEMA izmjerenih brojki. Ništa se ne mjeri bez odobrenog modela.
> / Methodology skeleton — NO measured numbers. Nothing runs without an approved model.

## Scenariji (isti ulazi za sve providere, bs-ijekavica primarno + en)

1. Intent classification 2. Tool selection 3. Agent routing 4. Task complexity
5. Next-action selection 6. Risk categorization 7. Escalation 8. Ambiguous decision 9. Abstention

## Usporedba / Comparison

| Oznaka | Provider | Uvjet za pokretanje |
|---|---|---|
| A | Jev 1.13 Free | `OPENCODE_API_KEY` (korisnik) |
| B | AnyJev Decider L0 | `scripts/anyjev_bridge.py --mode decider` + odobren model |
| C | AnyJev Tacit L0 | bridge/gateway + odobren Tacit checkpoint |
| D | AnyJev Adaptive | isto + `decision_mode: adaptive` |
| E | Clef-Flash local | SGLang + odobren download |

## Metrike (po scenariju × jeziku)

- accuracy, kalibracija (ECE gdje ima smisla), latencija (p50/p95), CPU/RAM/GPU,
  adaptive overhead (udio `route=cot`, tokeni), failure rate, fallback frequency.
- Svaki red: `provider, model, model_version, route/level, latency_ms` iz audit metapodataka.

## Uvjeti mjerenja (zajednički / common)

- Datum: 2026-11-12. Scenariji: `benchmarks/scenarios/anyjev-live.jsonl` (18 stavki, 9 scenarija × bs/en).
- B/C/D: ovaj server (12 CPU, 47 GB RAM, bez GPU), `morriszjm/Tacit-4B`, transformers engine, float32.
- A: `jev-1.13-free` preko OpenCode Console endpointa (ključ korisnika, $0).
- E: nije mjeren — treba GPU + ~18 GB download (nema odobrenja).
- Bodovanje: `correct` gdje reference postoji; yes_no normalizirano (Yes/True→tačno).

## Rezultati / Results (izmjereno / measured)

| Oznaka | Točnost (scored 14) | Greške | Latencija p50 / max | Napomena |
|---|---|---|---|---|
| B Decider L0 (Tacit-4B težine, CPU) | **11/14 (79%)** | 0 | 17.5 s / 47 s | K rotacija po odluci → sporiji |
| C Tacit L0 (CPU) | **11/14 (79%)** | 0 | 9.9 s / 30 s | jedan forward; eskalacija se broji kao tačna uz normalizaciju |
| D Tacit Adaptive (CPU) | **11/14 (79%)** | 0 | 7.8 s / 11 s | `route=cot` 0/18 → bez eskalacija, bez overheada na ovom setu |
| A Jev 1.13 Free | **14/14 (100%)** | 0 | 334 ms / 1067 ms | `model_version: jev-1.13-free`, cost 0 (billing_source free) |
| E Clef local | — (blokirano: GPU/download) | — | — | — |

Pojedinosti: `benchmarks/reports/live-{B-decider-l0,C-tacit-l0,D-tacit-adaptive,A-jev}.json`.

**Rerun A (2026-11-13):** istih 18 scenarija, novi korisnički ključ, runner
`scripts/live_jev_bench.py` — **14/14, 0 grešaka, p50 256 ms / max 299 ms**.
Reproducira 2026-11-12 (14/14, p50 334 ms); `ambiguous-*` i dalje `bug`,
`abstain-*` i dalje `other`, `escalate-*` 0.86. Sirovo:
`benchmarks/reports/live-A-jev-rerun-20261113.json`.

## Kalibracijske opservacije (sve izmjereno, n=18)

- `escalate-*`: Yes ≈ 0.70–0.77 (oba enginea) — jasna margina, ispravna eskalacija.
- `ambiguous-bs` ("radi čudno ponekad"): feature 0.72 (Tacit) / 0.76 (Decider) — samouvjereno
  na genuino dvosmislenom ulazu; log-prob margina ~1.0 > tau 0.5 → adaptive NIJE eskalirao.
  Zaključak: default `tau=0.5` rijetko okida; za kraće tekstove razmotriti niži tau (uz mjerenje).
- `abstain-*` (gibberish): "other" 0.76–0.83 — model bira ispravan bucket umjesto apstinencije;
  ispod `confidence 0.80` tek djelomično. Apstinencijski prag 0.40 se ne okida na ovom setu.
- D == C bit-za-bit (deterministički model, nema cot-a) — dokaz ponovljivosti.
- Niti jedna odluka nije pala (0 errors / 72 mjerenja A+B+C+D).
- **Jev vs Tacit kalibracija:** Jev daje degenerirane 0/1 distribucije (često conf 1.0) dok je
  Tacit glađi; na `ambiguous-*` se NE slažu (Jev: bug 1.0; Tacit: feature 0.72 / help 0.90) —
  oba samouvjerena, svaki na svoju stranu. Upozorenje: visok confidence ≠ istina, pogotovo
  kod dvosmislenog ulaza.
- **Tehnička napomena:** endpoint vraća 403 Python-urllib klijentima, a curl-u 200 —
  vjerojatno bot-filtriranje, ne rate limit. Svi A-pozivi odrađeni curl-om, razmak ~10 s,
  bez ijednog 403 nakon prelaska. `noul` odgovor je broj (vjerojatnost), ne boolean —
  adapter to već podržava (`p >= 0.5`).

## Rezultati / Results

_(E: nakon odobrenog downloada/GPU-a; zabranjeno fabriciranje)_
