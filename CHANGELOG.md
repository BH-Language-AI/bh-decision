# CHANGELOG — Decision Intelligence

## Unreleased — Plugin UX komande

- Plugin: `/decision-risk <zadatak>` (risk_level + needs_approval), `/decision-rank <zadatak> | opt1, opt2, opt3` (min. 2 opcije); `provider=<id>` prefiks sada na sve tri komande; zajednički jednolinijski ispis.
- Skill: dokumentirane nove ručne komande sa sintaksom.
- Testovi: 45 zeleno (43 + 2 nova za rank-usage i risk-fallback).

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
