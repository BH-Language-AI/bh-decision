# BH-Decision-2 (Tacit linija) — baseline i plan (2026-11-16)

> Linije po odluci korisnika: bh-decision-1 = EU/Ministral, bh-decision-2 = Tacit-4B.
> Tacit težine Apache-2.0 (Qwen3 baza — eksperimentalna linija, ne temelj BH-Decision).

## Baseline (mjereno, lokalni CPU)

- Stock `morriszjm/Tacit-4B`, transformers, float32, one_forward: **held-out 7/19 (37%)**,
  0 grešaka, p50 ~7 s. Metar za "prije".
- Naš najbolji Ministral SFT: 5/19 (26%). Tacit stock je trenutno najbolji lokalni rezultat.

## Trening plan (bh-decision-2)

- Baza: Tacit-4B backbone kao causal LM (config kaže Qwen3 arhitektura — radi na LUMI
  transformers 5.19 bez upgradea; joint head se ne dira).
- Podaci: `datasets/bh-decision-2/train.jsonl` (8474: naši šabloni format-sidro +
  200 human + thinking 500 + confirmation 800 + bosnian-core uzorak 2000).
- Cilj: popraviti held-out iznad 7/19 uz očuvan format 1.0; joint head evaluacija naknadno.
- Rizik (iskreno): SFT backbonea može pokvariti joint head readout — provjeriti nakon treninga
  AnyJev readoutom na istoj held-out listi.

## Mix v2 (2026-11-16, spreman — čeka GPU odobrenje)

- `scripts/build_bh2_mixv2.py` (seed 7): od v1 miksa (8474) van 3300 ne-JSON
  zapisa (1300 think-tragova + 2000 bosnian-core spama — provjereno travel/ISO
  ekavski boilerplate, nula decision sadržaja), o2 subsample 1744→1559 (= o1).
  Izlaz: `datasets/bh-decision-2/train-v2.jsonl` (4989, samo JSON ciljevi) +
  `manifest-v2.json`. Sljedeće: LoRA run + readout provjera, SAMO uz odobrenje.
- Validacija mixa v2 (offline, 2026-11-16): format 1.0 (4989/4989 validan JSON
  s `decision`), en udio ~8.4% (vidljiv), held-out leakage 0/20, think ostataka 0.
- Kernel `kaggle/bh2-mixv2/` spreman (commit 471358c); push 2026-11-16 odbijen —
  Kaggle GPU quota puna (qwen35-2b-fc QUEUED). Retry uspio iz 2. pokušaja (~19:20 UTC); kernel QUEUED na T4, watcher u pozadini.
- LUMI pokušaj (2026-11-16): oba SSH puta mrtva — EFP cert istekao (treba refresh
  na sshca.my-eurohpc.eu portalu), klasični `lumi` host ima placeholder username.
  BLOKER: korisnik mora osvježiti EFP cert. Kad SSH proradi, staging + submit:
  `train_grana_p.py` već čita `{"text": ...}` linije pa je kompatibilan s train-v2
  bez izmjena; submit: `sbatch slurm/grana-p-v2/grana-p-v2.sbatch <jobdir> morriszjm/Tacit-4B`
  uz jobdir s `train_grana_p.py + data/train-v2.jsonl + data/heldout-v1.jsonl`.
- Kaggle run GOTOV (2026-11-17, T4, ~2.5h): val 0.124, format 10/20 (0.5),
  held-out 2/10 — gore od stocka 7/19 i od v1 adaptera. o2-default na 19/20:
  prior je strukturni, subsample ne pomaže. Izvještaj: `docs/training/bh-decision-2-v2-2026-11-16.md`.
  **Linija 2 SFT pauzirana.** LUMI rerun otkazan kao nepotreban (pad nije T4 artefakt
  koji bi mijenjao odluku — format se raspao, a to je backbone/SFT interakcija).

## Human v06 + mix v3 (2026-11-17, trening se nastavlja)

- `datasets/expanded-v06/` (200 stavki, 100 bs + 100 en, manifest-v0.6):
  plauzibilni distraktori (heldout-stil), balans referenci o1 50 / o2 50 / o3 100 —
  prvi set koji napada o2-prior podacima, ne subsampleom. Balans izveden swapom
  ID-eva (tekst i rationale ostaju, mijenja se samo nosilac tačnog odgovora).
- `scripts/build_bh2_mixv3.py`: mix v3 = train-v2 + v06 → `train-v3.jsonl` (5189),
  dist o1 1609 / o2 1609 / o3 678, en ~10.2% (prag zadovoljen), leakage 0/20, think 0.
- HF: `bs-decision-bh2-mixv3-v01` + `bs-decision-human-v02` objavljeni.
- Kernel `kaggle/bh2-mixv3/` (pin 3d7ef39): push BLOKIRAN — tjedna GPU kvota 30h
  potrošena (mixv2 run + qwen jobovi). Retry svakih 12h u pozadini (7 dana);
  LUMI proradio preko Oracle skočnog čvora (agentmujo-training worker docs); job stagean na scratch, sbatch čeka QOS slot (amj-train oslobađa dev-g za ~50 min); submit USPIO — job 23816816 bh2-mixv3 RUNNING na dev-g (krenuo ~14:00 UTC); watcher prati do metrika.

## Korak-2 proba v2 (2026-11-16, gotova)

- Popravljen dizajn: 12 novih situacija sa state-specific opcijama
  (`scripts/selfdistill_probe_v2.py`, sirovo `datasets/selfdistill/probe-v2.jsonl`).
- Rezultat: **12/12 pogodak, ali cot=0/12, confidence ~0.99** — distraktori su
  apsurdni (npr. "ostaviti ključ pod otiračem"), pa model bira razumnu opciju
  po površinskoj formi, bez reasoninga. Test je prelagan: ne dokazuje da model
  može generisati vlastite trening podatke, samo da razlikuje razumno od
  apsurdnog. Degenerisani confidence (sve ~1.0) je isti fenomen kao kod Jev-a.
- Napomena o pristrasnosti: autor proba i referentnih odgovora je eksperimentator
  (ista ograda kao A/B v6 Muse grana) — gornja granica, ne nezavisna mjera.
- Pravi Korak-2 test traži uvjerljive distraktore (heldout-stil, sve opcije
  plauzibilne) = isti autorski posao kao human podaci. Pauzirano dok human
  pool ne naraste; v2 ostaje kao negativna kontrola dizajna probi.

## LUMI v3 run GOTOV (2026-11-17, job 23816816, 1:11, bf16)

- val 0.0999, strogo format 1/20 + 0/1 (trailing garbage reže strogi parse),
  tolerantno 6/19 (32%), o2-default slomljen (9/20).
- Izvještaj: `docs/training/bh-decision-2-v3-2026-11-17.md`.
- **SFT linije zatvorene** (mehanizam dokazan, 3 poraza od stocka, memorizacija).
- Kaggle retry3 otkazan — v3 već odrađen na boljem hardveru.

## Objava v0.1 (2026-11-18)

- Adapter (127MB, LoRA r16) objavljen na `BH-Language-AI/bh-decision-2-4b` (HTTP 200).
- Model card iskren: 6/19 ispod stocka 7/19, istraživački artefakt, ne za produkciju.
