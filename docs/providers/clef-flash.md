# Clef-Flash 9B — provjereni tehnički profil / Verified technical profile

> Provjereno 2026-11-12 iz: `huggingface.co/Cloudflare/clef-flash`,
> `developers.cloudflare.com/workers-ai/models/clef-flash`, `github.com/Cloudflare/clef`
> (projekt postoji / project exists). / Verified from official sources.

## Licenca i porijeklo / License and provenance

- **Licenca: Apache-2.0** (datoteka `LICENSE` u repozitoriju modela). Uvjeti: zadržati
  licencu i napomene; nema copyleft obaveze za naš kod. / Keep license attributions.
- Baza: `Qwen/Qwen3.5-9B` (+ vision encoder); safetensors shardi + `joint_head.safetensors`
  + `joint_schema_model.py` (custom code — potreban `trust_remote_code` kod lokalnog
  transformers pristupa). Veličina: 9B, BF16.
- **API potpuno kompatibilan sa Jev/SystemOne**: isti `state` + `questions`
  (`noul`/`choice`/`score`) format; SGLang služi na `/v1/systemone`.
  Jedan builder zahtjeva za Jev i Clef. / Fully Jev-compatible — one request builder.

## A. LOKALNO / LOCAL

- Podržani runtimes: Transformers (`joint_schema_model.systemone`), SGLang
  (`sglang:dev-clef` image, `/v1/systemone`), vLLM, Docker Model Runner.
- Ovaj server: 12 CPU, 47 GB RAM, **bez GPU**. 9B BF16 (~18 GB) stane u RAM;
  CPU inferenca je moguća ali ⚠️ latencija neizmjerena — obavezan benchmark prije
  produkcijske tvrdnje (Faza 6). Praktičan put: SGLang/transformers na CPU za pilot,
  GPU kasnije ako metrike opravdaju. / CPU possible, latency unmeasured — must benchmark.
- Kvantizacija: 63 community kvanta na HF su **chat-style** (llama.cpp/Ollama/LM Studio),
  ⚠️ NE izlažu SystemOne protokol — služe samo kao eksperimentalni fallback za grubu
  klasifikaciju tekstom, ne kao ravnopravna zamjena. Zvanični SystemOne lokalni put je
  puni model + joint head. / Community quants are chat-style, not SystemOne — experimental only.
- Bez preuzimanja modela bez odobrenja (pravilo projekta). / No downloads without approval.

## B. HOSTED

- Workers AI: `@cf/cloudflare/clef-flash`, kontekst 24.576 tokena, zero data retention,
  **cijena $0.038 / 1M ulaznih tokena — plaćeno**. ⚠️ Nije pronađena potvrđena besplatna
  kvota → `clef_hosted_free.enabled: false` po defaultu; omogućiti samo uz eksplicitno
  odobrenje i dokumentiran free-tier dokaz. / No verified free quota → disabled by default.
- Community hosted endpointi: samo eksperimentalno, nikad kao garantirana usluga.
- Referentna latencija (Decision Index): medijan ~39 ms, p95 ~122 ms (GPU-hosted);
  vlastita mjerenja u Fazi 6. / Own measurements in Phase 6.

## H3354 benchmark referenca / Benchmark reference

Javni Decision Index (40+ benchmaraka): Clef-Flash vodi ili parira Jevu na
classification/rutiranju (BFCL 98.8, API-Bank 93.1, RouterBench 79.9), slabiji na
CLINC150+OOS i RAGTruth — relevantno za `decision_route`/`decision_classify` dizajn
upitnika u Fazi 2/6. To su tuđe brojke; naše mjerimo sami. / Their numbers; we measure our own.
