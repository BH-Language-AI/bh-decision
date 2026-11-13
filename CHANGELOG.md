# CHANGELOG — Decision Intelligence

## Unreleased — Nezavisna analiza (8 tačaka)

- P1 metrike: `status()` sada vraća p50/p95 latenciju, broj eskalacija, keš hitove i
  precheck pokrivenost (`hits/misses/coverage`); glavna metrika ostaje ukupno vrijeme
  i tokeni po zadatku — naš dio se mjeri, agentski dio je izvan ovog sloja.
- P2 kontekst: opisi 14 alata skraćeni 1017→511 znakova (~254→~127 tokena, −50%);
  potpuno sažimanje 14→3-4 alata odgođeno jer je breaking change (testovi + skill + docs).
- P3 auto-hook: NIJE izvodljivo — instalirani `@opencode/plugin` nema hook/event API
  (`tool.execute.before` ne postoji u dist tipovima); rizik-gate ostaje ručni/MCP.
- P4 pravila: novi `packages/decision-core/src/precheck.ts` (6 obrazaca: rm -rf, SQL
  DROP, git push --force, delete-database, obriši-bazu, format/mkfs); `decision_assess_risk`
  i `/decision-risk` prvo pitaju pravilo (0 ms, 0 tokena), pokrivenost se loguje.
- P5 lokalna ruta: preskočeno po direktivi — samo Jev Free, ništa drugo.
- P6 kalibracija: bez koda — Jev vraća degenerirane 0/1 confidence pa se scaler nema na
  šta fitati (nema označene varijanse); pragovi ostaju, preporuka je eksplicitno
  `noul` pitanje dostatnosti (već dokumentirano).
- P7 keš: ključ normaliziran (mala slova + jedan razmak), hit rate u `status()`;
  bez perzistencije na disk iz privatnosti (taskovi mogu sadržavati tajne).
- P8 paralelizam: SKILL.md dopunjen — risk-procjena paralelno s prikazom odobrenja.
- Jev-only default: `fallback: []` (bilo `clef_local`); `decision.example.yaml` usklađen.
- Testovi: 51 zeleno (45 + 5 precheck + 1 plugin rule-hit).

## Unreleased — Plugin UX komande

- Plugin: `/decision-risk <zadatak>` (risk_level + needs_approval), `/decision-rank <zadatak> | opt1, opt2, opt3` (min. 2 opcije); `provider=<id>` prefiks sada na sve tri komande; zajednički jednolinijski ispis.
- Skill: dokumentirane nove ručne komande sa sintaksom.
- Testovi: 45 zeleno (43 + 2 nova za rank-usage i risk-fallback).
- Skill: ručni primjeri za `/decision-risk` i `/decision-rank` + napomena o zarezu.

## 0.1.0 (2026-11-12) — Faze 1–6

- Faza 1: discovery — Jev Free, Clef-Flash, plugin API v2.2.7, skill format, MCP SDK
  provjereni iz službenih izvora; korekcija tipova (`noul/choice/score`).
- Faza 2: `packages/decision-core` — normalizacija, registar s denylistom plaćenih,
  fallback lanac, dedup/keš/breaker/budžet, metrike, redakcija tajni.
- Faza 3: `packages/decision-mcp` — 11 `decision_*` alata, stdio transport.
- Faza 4: `skills/decision-intelligence/SKILL.md` (dvojezična operativna pravila).
- Faza 5: `packages/opencode-plugin` — registracija skilla+MCP, `/decision`,
  `/decision-status`; bez auto-hookova (namjerno, protiv latencije po zahtjevu).
- Faza 6: 29 testova zeleno; harness smoke p50 8 ms; live mjerenja čekaju ključeve.
- Greške pronađene testovima i ispravljene: breaker-reset bug, redactSecrets regex.
