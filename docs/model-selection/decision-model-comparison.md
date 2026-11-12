# Poređenje Decision modela — FAZA 1

Status: istraživački nacrt, FAZA 1. Ništa nije zaključano bez pilot mjerenja.
Datum: 2026-11-12. Kontakt: xnetba@gmail.com.

## 1. Kandidati

### Liquid AI d1 (d1-3B, d1-omni-600M; novije d1-2B / d1-Omni-2B)
- Autor: Liquid AI, Inc. (MIT spinout). Objava 7.10.2026.
- Arhitektura: nije generativan — jedan forward pass, nula output tokena, tipizirani odgovori (`noul` / `choice` / `score`). d1-3B (3,12B, SigLIP2 vision 400M, 32k kontekst, 128k vocab) post-treniran iz LFM2.5-VL-3B (hibrid konvolucija + pažnja); d1-omni-600M (587M) iz LFM2.5-Encoder-350M.
- Težine: da, HF `LiquidAI/d1-3B`, `LiquidAI/d1-omni-600M`.
- Licenca: LFM Open License v1.0 (Apache 2.0 baza + klauzula 5). Nije OSI-open-source u strogom smislu.
- Komercijala: besplatno ispod 10M USD godišnjeg prihoda pravnog lica, iznad treba plaćena licenca (`sales@liquid.ai`). Fine-tune dozvoljen, distribucija uz atribuciju.
- Bosanski: NEPOTVRĐENO — službeno podržani jezici LFM2 porodice ne uključuju bs/hr/sr.
- Benchmark: Decision Index 0.2.1: d1-3B 48,57 (najbolji ispod 10B).
- Izvori: https://huggingface.co/blog/LiquidAI/open-d1, https://huggingface.co/LiquidAI/d1-3B, https://www.liquid.ai/blog/d1-open, https://docs.liquid.ai/lfm/getting-started/model-license.md

### Strands Decider (AWS Strands Labs)
- Autori: strands-labs (AWS/Strands Agents eksperimentalni program), objava 1.10.2026 (Brooker, Chambers, Nonato de Paula).
- Arhitektura: dekoderski LLM trup + odbačena LM glava + pointer-glava (~1M param) + rank-16 LoRA. Tri tipa pitanja iz istog maskiranog softmaxa: `noul`, `choice`, `score`. Ref. model v1 1,9B (mix 246.678 redova, teacher gemma-4-31B-it, soup 3 seeda + kalibracija). Postoje E2B/E4B/12B/26B-A4B varijante. Kontekst 3–4k.
- Težine + pun recept: da — HF org `StrandsAgents`, kod/podaci/skripte u repou.
- Licenca: Apache 2.0 za kod, recept, podatke i checkpointove.
- Komercijala / FT / distilacija: da / da / da. Retrain ~11h na 1× RTX 3090 ili ~1h10 na 8× H100.
- Bosanski: NEPOTVRĐENO (naslijeđe Qwen3.5 navodno pokriva 201 jezik uključujući bs/hr, ali Decider kartica ne deklarira niti mjeri bs/hr/sr — treba vlastiti eval).
- Benchmark: JevBench v1: 180/231 (77,9%), Brier 0,280; Decision Index 12B 47,14 / 26B-A4B 48,69; kalibracija ≥0,9 confidence ≈ ~95% tačnosti na kratkim zadacima.
- Izvori: https://github.com/strands-labs/strands-decider, https://huggingface.co/StrandsAgents/strands-decider-2B-hobson-v19, https://strandsagents.com/blog/introducing-strands-decider/

### TypeSafe Jev (typed decision referenca)
- Autor: TypeSafe AI. Lansiran 15.9.2026 kao "System One model".
- Arhitektura/parametri: zatvoreno — težine i broj parametara nisu objavljeni (NEPOTVRĐENO). Metoda navedena kao RLCD. Hosted API (`state` + `Choice` do 255 opcija, `Score`, `Noul`, `Box`), 64k/zahtjevu.
- Licenca: nema težina; pay-per-token API (~0,042 USD/M inputa). Nema fine-tunea; distilacija outputa u drugi model pravno rizična / katalozi navode "Distillable: No" — provjeriti ToS prije ikakvog teacher korištenja.
- Bosanski: NEPOTVRĐENO — "engleski primaran, ostali handled but not equally well"; v1.14 donosi multijezični dobitak ali bez per-jezik brojeva.
- Benchmark: Decision Index lider (Jev 1.13: 58); Arize ROC AUC 0,93 na oba polariteta.
- Uloga u BH-Decision: samo hosted referentni baseline, ne baza i ne teacher bez pravne provjere.
- Izvori: https://typesafe.ai/blog/introducing-system-one-models-and-jev, https://docs.typesafe.ai/models

### Cloudflare Clef (clef 27B, clef-flash 9B) — NOVO, provjereno 2026-11-12
- Autor: Cloudflare. Objava: https://blog.cloudflare.com/clef-decision-models. Leaderboard: https://clef-evals.workers-ai-mle.workers.dev.
- Arhitektura: dekoderski trup + joint schema head (mala transformer glava: čita finalne hidden states, rutira dokaze iz statea na svako pitanje, skorira sve opcije svih pitanja zajedno). Jedan forward pass, tipizirani izlazi `noul` / `choice` / `score`, bez generisanja teksta. API potpuno kompatibilan s Jev/SystemOne (`POST /v1/systemone`; SGLang služi na `/v1/systemone`). Ulaz: state (string/JSON) + opciono slike/video; `max_length` default 16.384 tokena.
- Baze: clef = Qwen3.8-27B + vision enkoder; clef-flash = Qwen3.5-9B + vision enkoder. Zbog toga NE mogu biti finalne baze BH-Decision (pravilo: bez Qwen trupova kao konačne osnove) — ali su pravno čiste za proučavanje i baseline jer su i baze i post-trening Apache 2.0.
- Težine: da, HF `Cloudflare/clef`, `Cloudflare/clef-flash` (standardni sharded safetensors + `joint_head.safetensors` + `joint_schema_model.py` s `load_release_model` i `systemone`). Postoji i treća varijanta clef-omni (audio/video; detalje provjeriti).
- Licenca: Apache 2.0 (i model i Qwen3.5/3.8 baze). Komercijala / FT / distilacija: da — najčistiji pravni profil od svih decision modela u ovoj analizi.
- Bosanski: NEPOTVRĐENO — kartice ne deklariraju bs/hr/sr; postoji nezavisni `TurkishDecisionBenchmark` Space (turski kao srodan aglutinativni jezik nije dokaz za bs) — zaključak: treba vlastiti ijekavski eval, po uzoru na taj Space napraviti bosanski pandan.
- Benchmark (Decision Index 0.2.1, interna Cloudflare mjerenja — tretirati kao vendor tvrdnju, ne nezavisnu evaluaciju): clef-flash vodi na BFCL (98,8), API-Bank (93,1), MMLU (91,8), ForecastBench Brier 10,6; clef vodi na BANKING77 (94,2), CLINC150+OOS (97,4), GSM8K (80,8), RAGTruth (79,4). Workflow evali (Typesafe Evals): invoice processing exact 64,7 (clef) vs 61,8 (Jev). Latencija: clef-flash medijana 38,8 ms vs Jev 524,1 ms.
- Izvori: https://huggingface.co/Cloudflare/clef, https://huggingface.co/Cloudflare/clef-flash, https://blog.cloudflare.com/clef-decision-models

### System One koncept (TypeSafe docs) — usvojeno kao terminološki okvir
- Model vraća tipizirane odluke + kalibrirane vjerovatnoće iz statea; ne piše odgovore, kod ni obrazloženja rezonovanja. Primitivi: Choice, Score, Noul, Box (Box je vezan za regije slike — van opsega BH-Decision dok nema vizuelnog tiera). Svako pitanje ima `instructions` + `criteria`; odgovori nose `confidence` pa kod odlučuje act vs escalate. Kalibracija se mjeri preko grupa predikcija, ne garantuje pojedinačan odgovor. Izvor: https://docs.typesafe.ai/concepts/system-one. Naš izlazni protokol v0.1 već pokriva Choice/Score/Noul + confidence + abstention — usklađen, Box ne uvodimo.

### Dopunski: Kev, Skywork-Reward-V2, ArmoRM
- Kev (Jared Palmer): open klon Jeva, Qwen3.5/3.8 + LoRA + pointer head, TypeSafe-kompatibilan API, 0.8B/4B/9B/27B, Apache 2.0, komercijala/FT/distilacija da. Kartica eksplicitno "English" → bs NEPOTVRĐENO. Held-out DI 27B 52,3. Izvor: https://github.com/jaredpalmer/kev
- Skywork-Reward-V2 (Skywork AI): Bradley-Terry reward 0.6B–8B, SOTA na reward benchmarkima. Qwen3-izvedeni: Apache 2.0 (dozvoljeno); Llama-izvedeni: Llama Community License (MAU >700M treba dozvolu + zabrana korištenja outputa za trening drugog LLM-a). Podaci dominantno engleski → bs NEPOTVRĐENO. Uloga: dopunski scorer, ne tipizirani decision API. Izvor: https://github.com/SkyworkAI/Skywork-Reward-V2
- ArmoRM-Llama3-8B (RLHFlow): multi-objektivni + MoE gating, RewardBench 89,0. Licenca llama3 (nekomercijalna ograničenja + zabrana distilacije) → ne preporučuje se. Izvor: https://huggingface.co/RLHFlow/ArmoRM-Llama3-8B-v0.1

## 2. Uporedna tabela

| Model | Parametri | Težine | Licenca | Komerc. | FT/distil. | BS dokaz | Napomena |
|---|---|---|---|---|---|---|---|
| d1-3B | 3,12B | Da | LFM Open 1.0 | <10M free | Da/Da | NE | najjači mali, prihodni prag rizik |
| Strands 2B | 1,9B | Da + recept | Apache 2.0 | Da | Da/Da | NEPOTVRĐENO | najbolji pravni + recept profil |
| Strands 12B/26B-A4B | 12B/26B | Da | Apache 2.0 | Da | Da/Da | NEPOTVRĐENO | teacher kandidati |
| clef 27B | 27B (Qwen3.8) | Da | Apache 2.0 | Da | Da/Da | NEPOTVRĐENO | baseline/teacher, ne baza (Qwen trup) |
| clef-flash 9B | 9B (Qwen3.5) | Da | Apache 2.0 | Da | Da/Da | NEPOTVRĐENO | isto; metodološki uzor za 9B tier |
| Jev | nepoznato | Ne (API) | komerc. ToS | pay-per-token | Ne/Ne | NEPOTVRĐENO | samo baseline |
| Kev 4B/27B | 4B/27B | Da | Apache 2.0 | Da | Da/Da | Ne (EN) | rezerva receptu |
| Skywork-R-Qwen3 | 0.6–8B | Da | Apache 2.0 | Da | Da/Da | NEPOTVRĐENO | dopunski scorer |

## 3. Zaključak FAZE 1 (decision sloj)

Lokalni decision sloj graditi na Strands Decider receptu (Apache 2.0, pun trening kod) ili Kevu kao rezervi, uz joint schema head iz Clefa kao drugi arhitektonski uzor (zajedničko skoriranje svih pitanja odjednom — provjeriti u pilotu da li tuče pojedinačne pointer glave). d1 tehnički najjači mali model, ali LFM prag od 10M USD je pravna zamka za Kolektiv/Gamatrade scale — koristiti samo za poređenje, ne kao bazu bez pravnog mišljenja. Clef/clef-flash (Apache 2.0, Jev-kompatibilan API) uvesti kao obavezne baseline u pilot i kao kandidate za decision teachere — ali NIKAD kao finalne baze jer su im trupovi Qwen. Jev samo kao hosted baseline. Prije FAZE 2 obavezan vlastiti bs-ijekavski mini-eval: nijedan vendor ne dokazuje bosanski.
