# Benchmark izvještaj Faze 6 / Phase 6 benchmark report (2026-11-12)

> Mjereno, ne tvrdnje bez pokrića. / Measured, no unfounded claims.

## Što je mjereno / What was measured

Harness smoke kroz stvarni MCP put (`decision_benchmark`, limit 20, uzorci iz
`datasets/samples/*.jsonl`): MCP roundtrip + Core (validacija, normalizacija, keš)
+ SystemOne HTTP prema **mock** provideru (deterministički prvi izbor).
To NIJE točnost Jeva ni Clefa — mock uvijek bira prvu opciju.

| Metrika | Izmjereno |
|---|---|
| Ukupno primjera / total | 20 |
| Zidno vrijeme / wall | 296 ms |
| Latencija po odluci p50 / per-decision p50 | 8 ms |
| Latencija max (hladan start) | 105 ms |
| Mock "accuracy" (samo ispravnost harness-a) | 0.40 — bez značenja za providere |
| Apstinencije | 0 |

## Dostupnost providera / Provider availability (ovaj server, bez ključeva)

- `jev`: nedostupan — `Missing OPENCODE_API_KEY` (očekivano, graceful).
- `clef_local`: nedostupan — ništa ne sluša na `:30000` (očekivano, graceful).
- Svi pozivi bez providera završavaju urednom greškom, server ostaje živ.

## Što NIJE mjereno (treba korisničke kredencijale / What was NOT measured)

- A/B/C/D poredba iz specifikacije (bez DI vs Jev vs lokalni Clef vs hosted).
  Razlog: nema `OPENCODE_API_KEY`, nema lokalnog SystemOne servera, nema verificiranog
  free hosted tiera. `tests/integration/live.test.ts` je spreman i preskače se bez ključa.
- Uticaj na glavni LLM (tokeni, trajanje zadatka) — treba agent-harness s fiksnim
  scenarijima; predloženo za DI Fazu 7.
- CPU latencija pravog Clef-Flasha 9B — treba SGLang/transformers + odobrenje za download.

## Zaključak

Harness radi end-to-end (29 testova zeleno), overhead Core+MCP je reda milisekundi
uz mock provider. Tvrdnje o brzini/točnosti providera se NE iznose dok nema live mjerenja.
