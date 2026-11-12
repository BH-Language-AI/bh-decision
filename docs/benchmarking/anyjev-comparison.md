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

## Rezultati / Results

_(prazno — popuniti nakon odobrenih pokretanja; zabranjeno fabriciranje / empty — fill after approved runs; no fabrication)_
