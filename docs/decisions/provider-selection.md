# Odluka o izboru providera / Provider selection decision

> Faza 1, 2026-11-12. Status: prijedlog, čeka odobrenje za Fazu 2.
> / Phase 1. Status: proposal, awaiting approval for Phase 2.

## Preporučeni redoslijed / Recommended order

1. `jev` (Jev 1.13 Free, hosted) — primarni, dok je ponuda aktivna.
2. `clef_local` (Clef-Flash 9B, SystemOne lokalno) — prvi fallback, podaci ostaju lokalno.
3. `clef_hosted_free` — **onemogućen po defaultu**; samo uz dokazan free tier + odobrenje.
4. `future_bh_decision_{2b,4b,9b}` — konfiguracijski utori; **bez lažnih implementacija**,
   samo mock provideri u testovima. / Config slots; mocks in tests only.

## Nulti trošak — provedba / Zero-cost enforcement

- `allow_paid=false` je default i provjerava se na **dva sloja** (Core registry odbija
  registraciju/poziv plaćenog modela; MCP sloj ponovno provjerava prije slanja).
  Test `paid provider is never called` je obavezan u CI s mock mrežom.
- `DECISION_ALLOW_PAID` env override nikad ne smije postati `true` automatski niti tiho;
  promjena koja mijenja trošak/dijeljenje podataka zahtijeva eksplicitnu konfiguraciju.
  / Cost/data-sharing changes are never silent.
- Zabranjene mete: `jev-1.13` (plaćeni), `@cf/cloudflare/clef-flash` Workers AI
  (plaćeni, $0.038/1M) — popis u kodu kao denylist, ne samo u dokumentaciji.

## Prekidači / Switches (bez promjene koda / no code changes)

```yaml
providers:
  primary: jev
  fallback: [clef_local]
  allow_paid: false
```

`DECISION_PROVIDER`, `DECISION_FALLBACK`, `DECISION_ALLOW_PAID` nadjačavaju YAML.
Svaki provider se može onemogućiti pojedinačno; prioritet je lista, ne hardkod.
Pragovi (`confidence`, `escalation`, `timeout_ms`, `max_decisions_per_session`) su
konfigurabilni s dokumentiranim defaultima. / Env overrides YAML; per-provider disable.

## Zašto ovako / Rationale

- Jev Free: jedini danas provjereni $0 SystemOne endpoint; rizik = privremenost →
  pokriven fallbackom, ne ovisnošću. / Only verified $0 endpoint; temporariness covered.
- Clef lokalno: Apache-2.0, isti protokol, podaci ne napuštaju server — strateški fallback
  i put prema vlastitim BH-Decision modelima (ista SystemOne paradigma).
- Hosted Clef bez free dokaza ostaje isključen — cijena se ne pretpostavlja.
- Jezik: TypeScript Core+MCP+plugin (obrazloženo u `system-architecture.md`).
