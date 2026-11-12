# Jev 1.13 Free — provjereni tehnički profil / Verified technical profile

> Provjereno 2026-11-12 iz: `opencode.ai/docs/console/models`, `models.dev`
> (`typesafe/jev-1.13.0`), `docs.typesafe.ai`. / Verified 2026-11-12 from official sources.

## Identitet / Identity

- Model ID (free): **`jev-1.13-free`** — koristiti točno ovaj string, bez zamjena.
  / Use exactly this string, no silent substitution.
- Plaćeni pandan: `jev-1.13` — **zabranjen** dok je `allow_paid=false`.
  / Paid counterpart — **forbidden** while `allow_paid=false`.
- Endpoint: `POST https://opencode.ai/inference/systemone/v1/systemone`
- Auth: OpenCode Console API ključ (`Authorization: Bearer $OPENCODE_API_KEY`). Ključ je
  tajna iz okruženja, nikad u kodu/logovima. / Console API key from env, never in code/logs.
- Kontekst: 64.000 tokena; izlazni tokeni: 0 (nema generiranja teksta).
- Težine: **zatvorene (Closed)** — Jev je hosted usluga, NE open-source lokalni model.
  / Weights closed — hosted service, NOT an open local model.
- Cijena: Free = $0; plaćeni = $0.042 / 1M ulaznih tokena, izlaz free.
- Dostupnost: **"limited-time"**, bez objavljenog datuma isteka i bez SLA.
  Privatnost za Free tier: ⚠️ nije dokumentirana zero-retention politika (za razliku od
  nekih drugih free modela) — zato minimalni state + `send_repository_content: false`.
  / No documented zero-retention for the free tier — hence minimal state.

## Format zahtjeva / Request format (stvarni / actual)

```json
{
  "model": "jev-1.13-free",
  "state": "string ili JSON / string or JSON",
  "questions": {
    "is_urgent": { "type": "noul", "instructions": "..." },
    "department": { "type": "choice", "instructions": "...",
      "criteria": { "returns": "...", "shipping": "..." } },
    "frustration": { "type": "score", "instructions": "...", "criteria": ["Calm", "..."] }
  }
}
```

Tipovi: samo `noul | choice | score` (+ `box`, irelevantan za nas).
`instructions` opcionalan. Do 64 pitanja po zahtjevu; pitanja se evaluiraju paralelno.
Naš interni `categorical` → `choice`, `boolean` → `noul`. / Our internal types map to these.

## Format odgovora / Response format

`{ "model": "...", "answers": { "<id>": {...} }, "usage": {...} }` —
`choice` daje `choice/confidence/probabilities`, `score` daje
`score/confidence/legend/probabilities`, `noul` daje vjerojatnost true.
Snimiti vraćeni `model` (verziju) u audit metapodatke. / Record returned model version.

## Greške / Errors

Obraditi: 401/403 (ključ), 429 (rate limit — backoff + fallback), 5xx/timeout
(fallback lanac). Plaćeni `jev-1.13` se nikad ne poziva automatski.
Referentna latencija (Decision Index, interno mjerenje Cloudflarea): medijan ~524 ms —
mjeriti vlastitu u Fazi 6, ne preuzimati. / Measure our own in Phase 6.
