# Odluka: integracija AnyJev / AnyJev integration decision

> 2026-11-12. Status: implementirano iza plana, testovi zeleni (43 TS + 19 Python).
> / Implemented per approved plan, tests green.

## Odluka / Decision

AnyJev postaje **opcionalni, zamjenjivi decision engine** (`anyjev_local`) unutar postojećeg
ProviderRegistry — bez promjene jezgra, protokola, MCP sučelja ili arhitekture plugin-a.
Default: **isključen** (`enabled: false`, prazan `model` = neregistriran). Ništa se ne mijenja
za postojeće Jev/Clef rute dok korisnik eksplicitno ne uključi AnyJev.

## Zašto ovaj dizajn / Rationale

- `IProvider.decide(SysRequest)` + `fromSystemOne` već pokrivaju sve što treba: adapter samo
  prevodi SysRequest → `/v1/decide` → SysResponse. Nula promjena u `core.ts`/`systemone.ts`.
- AnyJev je Python, Core je TS → jedan HTTP ugovor (stock `anyjev.serve` ili naš
  `scripts/anyjev_bridge.py` za Decider/transformers). Nula novih TS ovisnosti.
- Generički MCP alati i plugin rade automatski jer idu kroz `core.decide`.
- 26-opcija i 10-nivoa limiti AnyJeva se **eksplicitno odbijaju** (`unsupported`), ne simuliraju.
- Qwen-bazirani Tacit modeli: samo eksperimentalni benchmark, nikad temelj BH-Decision-2B/4B/9B.

## Što je dodano / What was added

- `packages/decision-core/src/providers/anyjev.ts` — adapter + `configure()` allowlist.
- `scripts/anyjev_bridge.py` — lokalni `/v1/decide` server (tacit/decider, stdlib HTTP).
- `config.ts`/`providers.ts` — `anyjev` konfiguracija, `ANYJEV_*` env, registracija uz model.
- MCP: `decision_anyjev_status`, `decision_anyjev_config`, `decision_anyjev_test` (11→14 alata).
- Plugin: `/decision provider=<id>` jednokratni ručni izbor.
- Skill: `## AnyJev Decision Engine` + 9-koraka operativna politika.
- Testovi: `tests/core/anyjev.test.ts` (14 slučajeva, mock mreža).

## Blokirano / Blocked (treba korisnik)

- Stvarni model: `pip install "anyjev[hf]"` + download (npr. `morriszjm/Tacit-4B`, ~8 GB) — bez odobrenja.
- Live benchmark A–E (`docs/benchmarking/anyjev-comparison.md` je kostur bez brojki).
- Objave — samo uz eksplicitno odobrenje.
