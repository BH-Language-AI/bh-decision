# Release checklist — Decision Intelligence v0.1.0

> Ništa se ne objavljuje bez eksplicitnog odobrenja. / Nothing ships without approval.

## Gotovo / Done (2026-11-12)

- [x] Core, MCP (11 alata), skill, plugin — 29 testova zeleno
- [x] Plugin se učitava u pravom OpenCode v2.2.7 (`plugin list` → `bh-decision`)
- [x] MCP auto-registracija radi (`mcp list` → `bh-decision connected`)
- [x] MCP sheme verificirane kroz SDK klijenta (11 alata)
- [x] Graceful pad bez ključeva (uredna MCP greška, server živ)
- [x] Nema tajni u isporučenom kodu (automatski test)
- [x] Docs: arhitektura, protokol, provideri, instalacija, privatnost, metodologija
- [x] Harness smoke: p50 8 ms (mock), izvještaj `benchmarks/reports/phase-6.md`

## Čeka / Pending (treba korisnik)

- [ ] Live `jev-1.13-free` poziv — treba `OPENCODE_API_KEY` (`live.test.ts` spreman)
- [ ] Agent-izvršenje `/decision-status` — lokalni modeli preslabi/prespori na CPU-only
      serveru (qwen3:0.6b ne slijedi komande, qwen3:4b >240 s); probati uz glavni model
- [ ] Lokalni Clef-Flash mjerenje — treba odobrenje downloada (~18 GB) + SGLang/GPU odluka
- [ ] A/B/C/D poredba iz specifikacije — nakon gornjeg
- [x] Repo je live: `BH-Decision` je git repo, `origin` = `github.com/BH-Language-AI/bh-decision`
      (povijest + push vodi paralelna trening-sesija; ovaj commit dodaje samo DI rename + checklist, bez pusha)
- [ ] GitHub repo `BH-Language-AI/BH-Decision` — SAMO uz odobrenje (remote ne postoji)
- [ ] Hugging Face objava — SAMO uz odobrenje
