# AnyJev — provjereni tehnički profil / Verified technical profile

> Provjereno 2026-11-12 iz: `github.com/nokia-applied-research/AnyJev` (README, `anyjev/*.py`,
> `pyproject.toml`, `docs/limitations.md`), `pypi.org/project/anyjev/`, HF API
> (`morriszjm/Tacit-*`). / Verified 2026-11-12 from official sources.
> Verzija / Version: **anyjev 0.3.0**. Status paketa: Pre-Alpha (PyPI classifier).

## Identitet / Identity

- **Što je:** Bayesov readout-sloj koji svaki otvoreni causal LM pretvara u Jev-stilski
  odluke: tipizirana pitanja + vjerojatnosti iz next-token logits, bez treninga, bez parsiranja.
  / Turns any open causal LM into Jev-style decisions, no training, no parsing.
- **Dva ulaza / Two ways in:**
  - `Decider` — training-free, bilo koji otvoreni model; razine `raw` i `L0` (default).
  - `Tacit` — samodestilirani checkpointi; jedan forward po odluci; `adaptive=True` šalje
    nesigurne odluke na vlastito reasoning (route `cot`), uz cap.
- **Nije povezan s TypeSafe AI / Jevom.** / Not affiliated with TypeSafe AI or Jev.
- **Licenca frameworka: Apache-2.0** (`LICENSE` u repozitoriju). / Framework license: Apache-2.0.

## API (stvarni, ne izmišljeni / actual, verified from source)

```python
from anyjev import Decider, Question, Tacit
from anyjev.backends.hf import HFBackend  # ili/or VLLMBackend, SGLangBackend(url, model), LlamaCppBackend(gguf)

d = Decider(HFBackend("Qwen/Qwen3-8B"))          # level="L0" default
route = Question.choice("Which team?", ["billing", "technical"], name="route")
r = d.decide("My card was charged twice.", [route])["route"]
r.distribution, r.level                          # {opcija: p}, "L0"

tacit = Tacit.from_pretrained("morriszjm/Tacit-9B", adaptive=True, tau=0.5,
                              max_cot_share=0.2, cot_window=1000)
t = tacit.decide(state="...", question="...", options=["a", "b"])   # kind="choice" default
t["answer"], t["probs"], t["route"]              # "a", {...}, "one_forward" ili/or "cot"
tacit.decide_batch([...])                        # lista dictova / list of dicts
```

- `Question`: `choice(text, options, name?)`, `noul(text, name?)`, `score(text, bins|levels, ...)`.
  Vrste: `choice | noul | score` (Tacit prima i `yes_no` kao alias za `noul`). /
  Kinds: `choice | noul | score` (Tacit also accepts `yes_no` = `noul`).
- `Decision`: `.distribution`, `.argmax`, `.answer`, `.confidence` (= max prob),
  `.p_true` (noul), `.value` (score, očekivanje), `.require("L0")` baca `LevelError`.
- `Decider`: `decide(state, questions, require=)`, `decide_batch(states, question)`;
  `adaptive_shifts=True` + `calibrate_adaptive(question, unlabelled_states)` = rotation budget
  (7.2 umjesto 18 rotacija, ~2.2× propusnost, bez labela). `SGLangBackend` postoji
  (doprinos @shentonyan), `LlamaCppBackend` postoji (doprinos @Tusm11).
- Gateway: `python -m anyjev.serve --model ... --upstream http://127.0.0.1:8000 --adaptive --port 8100`
  (samo stdlib; sluša 127.0.0.1; **bez autentikacije** — samo lokalno).
  `POST /v1/decide` (jedna odluka ili `{"items": [...]}`), `GET /v1/stats`, `GET /health`.

## Ograničenja (potvrđena, iz `docs/limitations.md`) / Confirmed limits

- Točnost ograničena modelom; readout ne dodaje znanje. / Accuracy bounded by the model.
- **Max 26 opcija** (letter readout) — naših internih 64 > 26 → adapter mora eksplicitno odbiti. /
  Max 26 options — adapter must explicitly reject more.
- Tacit one_forward čita opcije redom, bez rotacija (L0 na Tacit checkpointu = K prefillova, neizmjereno).
- Eskalirana (`cot`) odluka košta **sekunde, ne milisekunde** (do `cot_max_tokens` tokena); cap veže
  udio, ne trajanje jedne odluke. / Escalated decisions cost seconds; cap bounds share, not latency.
- Na vLLM-u Tacit čita labele iz top-20 logprobs; labela izvan top-20 = 0.
- Tacit-9B/2B (Qwen3.5) trebaju `transformers>=5`; vLLM na Hopperu treba `nvcc`.
- L0 batch prior gubi točnost kad jedna labela dominira batchem (`prior="content_free"/"none"`).

## Tacit modeli / Tacit models (HF-verificirano)

| Model | Baza / Base | Licenca / License |
|---|---|---|
| `morriszjm/Tacit-1.7B` | Qwen3-1.7B | Apache-2.0 (HF tag) |
| `morriszjm/Tacit-2B` | Qwen3.5-2B | Apache-2.0 (HF tag) |
| `morriszjm/Tacit-4B` | Qwen3-4B | Apache-2.0 (HF tag) |
| `morriszjm/Tacit-8B` | Qwen3-8B | Apache-2.0 (HF tag) |
| `morriszjm/Tacit-9B` | Qwen3.5-9B | Apache-2.0 (HF tag) |

- ⚠️ SVE baze su Qwen (ne-europske) → po politici projekta **samo izolirani eksperimentalni
  benchmark**, nikad temelj BH-Decision-2B/4B/9B. / All Qwen-based → experimental benchmark only.
- `AnyJev-Tacitus-31B` (Gemma-4-31B baza, Full 66.47) je **izvan opsega** integracije (nije tražen,
  Gemma licenca zasebna). / Out of scope.
- Brojke iz README-a (JevBench, bev-decision, Decision Index) su tuđe; naša mjerenja tek slijede,
  bez fabriciranja. / Their numbers; we measure our own.

## Backendi i naša infrastruktura / Backends and our infra

| Backend | Paket | Ovaj server (12 CPU, 47 GB RAM, bez GPU) |
|---|---|---|
| transformers (`hf`) | `anyjev[hf]`: torch + transformers | ✅ jedini praktičan lokalni put (CPU, sporo) |
| vLLM in-process / `vllm serve` | `anyjev[vllm]` | ⚠️ treba GPU; ovdje ne |
| SGLang | postoji backend | ⚠️ treba GPU; ovdje ne |
| llama.cpp GGUF | `anyjev[llamacpp]` | ⚠️ GGUF = samo chat-kvantovi? provjeriti — readout treba logprobs; eksperimentalno |
| Gateway `anyjev.serve` | stdlib, ispred `vllm serve` | ⚠️ treba vLLM upstream = GPU |

- Python ovisnost: baza samo `numpy`; `hf`/`vllm`/`llamacpp` su opcioni extra-i. Naš Core je TS →
  integracija ide preko (a) gateway HTTP ili (b) stdio bridge-skripte; bez novih TS ovisnosti.
- ⚠️ PRETPOSTAVKA (ne provjereno bez modela): točan JSON oblik `probs` za `yes_no`/`score` kroz
  gateway; adapter normalizira defenzivno i odbija malformirano — ugovor se pin-a našim mock testovima.
- Nema downloada modela bez odobrenja; nema GPU jobova; nema plaćenih poziva. /
  No downloads, no GPU jobs, no paid calls.
