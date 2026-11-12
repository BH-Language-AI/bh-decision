# Sistemska arhitektura / System Architecture — BH-Decision Intelligence

> Faza 1 (discovery), 2026-11-12. Činjenice provjerene prema službenoj dokumentaciji;
> pretpostavke su označene sa ⚠️. / Phase 1 (discovery), 2026-11-12. Facts verified
> against official docs; assumptions are marked ⚠️.

## 1. Slojevi / Layers

```
┌─────────────────────┐
│ OpenCode agent      │  skill: decision-intelligence (SKILL.md, bez koda / no code)
│ + plugin (opći)     │  plugin: poziva Core, nikad ne odlučuje sam / calls Core, never decides alone
└─────────┬───────────┘
          │ stdio (lokalno / local)
┌─────────▼───────────┐
│ MCP server          │  @modelcontextprotocol/sdk v1.32.2; 11 alata / tools
└─────────┬───────────┘
          │ čisti TS pozivi / pure TS calls
┌─────────▼───────────┐
│ Decision Core       │  bez OpenCode ovisnosti / no OpenCode dependency
└─────────┬───────────┘
          │ SystemOne protokol / protocol
┌─────────▼───────────┐
│ Provideri / Providers│ jev (hosted) → clef_local → clef_hosted_free → future_bh_*
└─────────────────────┘
```

## 2. Zašto TypeScript / Why TypeScript

- OpenCode plugin **mora** biti TS (`@opencode/plugin` v2.2.7, `Plugin.define`, provjereno na
  instaliranoj verziji). / The OpenCode plugin **must** be TS.
- MCP server: TS SDK je zreo i održavan; isti jezik = Core se dijeli bez prepisivanja.
  / TS SDK is mature; same language = Core shared with no rewrites.
- Core ostaje uvoziv iz bilo koje Node/Bun aplikacije, bez OpenCode importa.
  / Core stays importable from any Node/Bun app, with no OpenCode imports.

## 3. Protokol: koncept vs stvarnost / Protocol: concept vs reality

⚠️ KOREKCIJA: zadani koncept (`categorical`/`boolean`) **ne odgovara stvarnom API-ju**.
Stvarni SystemOne tipovi (provjereno: TypeSafe docs + Cloudflare Workers AI docs):

| Stvarni tip / Real type | Mapiranje koncepta / Concept mapping |
|---|---|
| `noul` (true/false + vjerojatnost) | `boolean` |
| `choice` (imenovane opcije + `probabilities`) | `categorical` |
| `score` (rubrika, očekivana vrijednost + `probabilities`) | ordinal / nivo složenosti |

Core normalizira: naš interni zahtjev (`task_type`, `complexity`, `requires_escalation`)
→ SystemOne `questions`; svaki provider odgovor → jedna interna shema
(`selected`, `probabilities`, `confidence`, `abstain`, `model_version`, `latency_ms`).
Jev i Clef-Flask su **potpuno kompatibilni** (isti `state`+`questions` format) —
jedan builder zahtjeva pokriva oba. / One request builder covers both.

Odgovor po pitanju (provjereno): `choice` → `choice/confidence/probabilities`;
`score` → `score/confidence/legend/probabilities`; `noul` → vjerojatnost true.
`instructions` je opcionalan; `images`/`videos` se NE šalju (privatnost, trošak).
/ Per-question answers verified; media fields are never sent (privacy, cost).

## 4. MCP server

- Transport: **stdio** (OpenCode integracija). Streamable HTTP opcionalan kasnije, nikad
  javno bez autentikacije. / stdio for OpenCode; HTTP later, never public without auth.
- 11 alata iz zadatka; svaki: stroge ulaz/izlaz sheme (Zod ili čisti JSON Schema —
  odluka u Fazi 3, ⚠️), timeout, provider metapodaci. / 11 tools; strict schemas, timeouts.
- MCP server NE poziva plaćene providere ako `allow_paid=false` — provjera na dva mjesta:
  Core registry + MCP sloj. / Double-gated paid-provider block.

## 5. Plugin (opća integracija / general integration)

Provjereno na `@opencode/plugin` 2.2.7: `Plugin.define({id, setup(ctx)})`, domene
`ctx.session` (hooks: `prompt`, `context`, `generate`, `title`), `ctx.tool`
(transform/add), `ctx.command`, `ctx.mcp`, `ctx.storage`, `ctx.permission`.
Kandidat-mehanizam za automatske odluke: `session` hook + `ctx.storage` dedup po sesiji
+ `ctx.experimental.generate.decisions` (⚠️ eksperimentalno, nativni Jev poziv
`{providerID:"opencode", id:"jev-1.13"}` — provjeriti ponašanje/limite u Fazi 5 prije odluke
MCP vs nativno). / Candidate mechanism; MCP vs native to be decided in Phase 5 spike.

Tvrda pravila (nepromjenjiva): plugin nikad ne autorizira destruktivne akcije;
sve dozvole ostaju OpenCode-ove; pri timeoutu/grešci → tihi nastavak bez odluke;
bez tajni i punih promptova u logovima. / Hard rules: never authorize destructive
actions; silent fallback; no secrets in logs.

## 6. Presijecanje poziva / Call discipline

- Deterministička pravila prije modela (jednostavni zadaci). / Deterministic rules first.
- Dedup po `(sessionID, hash(state+questions))`, limit odluka po sesiji, TTL keš,
  circuit breaker, odvojeni pragovi (tool/model/risk/escalation/abstain) iz konfiguracije.
  / Dedup, per-session budget, TTL cache, circuit breaker, configurable thresholds.
- Minimalni state: nikad cijeli repo ili historija chata provideru.
  / Never send full repo or chat history to providers.

## 7. Rizici i nepoznanice / Risks and unknowns

1. **Jev Free je privremen** ("limited-time", bez datuma isteka) — arhitektura to podnosi
   (fallback lanac), ali pratiti status. / Track its status.
2. **Lokalni Clef na CPU-u** (ovaj server: 12 CPU, 47 GB RAM, bez GPU): 9B BF16 stane u RAM,
   ali transformers-CPU latencija ⚠️ neizmjerena — mjeriti u Fazi 2/6 prije bilo kakvih tvrdnji.
   / CPU latency unmeasured — measure before any claims.
3. Community kvantizacije (63 na HF) su chat-style, **ne** SystemOne protokol — samo eksperimentalno.
4. Workers AI nema potvrđenu besplatnu kvotu za Clef → `clef_hosted_free` default **off**.
5. `ctx.experimental.generate.decisions` API se može promijeniti (eksperimentalno).

## 8. AnyJev (opcionalni engine / optional engine, 2026-11-12)

- `anyjev_local` je običan `IProvider` (default **off**): `SysRequest` → `POST /v1/decide`
  → `SysResponse`, pa postojeća `fromSystemOne` normalizacija radi bez promjena.
  Detalj: `docs/providers/anyjev.md`; adapter: `packages/decision-core/src/providers/anyjev.ts`.
- Dva lokalna servera iza istog ugovora: stock `python -m anyjev.serve` (Tacit + vLLM,
  treba GPU) ili `scripts/anyjev_bridge.py` (Tacit/Decider, transformers = CPU OK).
  TS strana ima nula novih ovisnosti (samo fetch).
- Limiti se odbijaju, ne simuliraju: choice >26 opcija i score >10 nivoa → `unsupported`.
- Qwen-bazirani Tacit modeli su samo eksperimentalni benchmark (vidjeti
  `docs/decisions/anyjev-integration.md`), nikad temelj BH-Decision-2B/4B/9B.
