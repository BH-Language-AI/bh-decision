# Pilot FAZE 5 — A vs B vs C

Status: specifikacija zamrznuta. Datum: 2026-11-12.
Izvršenje: `python3 scripts/pilot.py --arm {a,b,c}`; bez GPU-a samo `--dry-run` (podrazumijevan).

## 1. Krakevi

| Krak | Baza | Postupak |
|---|---|---|
| A | `StrandsAgents/strands-decider-2B-hobson-v19` | LoRA SFT (r=16, alpha=32, dropout=0.05) na seed podacima; glave se ne diraju |
| B | `utter-project/EuroLLM-1.7B` | Jezička adaptacija (ijekavski korpus, bs:en 75/25) + scoring/pointer glava iz `docs/architecture/decision-heads.md` |
| C | `utter-project/EuroLLM-1.7B` | Sve iz B + distilacija: teacher `Cloudflare/clef-flash` decision primjeri + `TildeOpen-30B` generisani ijekavski primjeri (tehnike 1–4 iz `docs/distillation/methodology.md`); svaki primjer nosi svih 6 provenance polja |

LoRA recept za sva tri kraka: r=16, alpha=32, dropout=0.05, moduli `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`, bf16, seed 42, batch 4×8, lr 2.0e-4, 3 epohe (vrijednosti iz `configs/2b.yaml`).

## 2. Podaci

- Seed: `datasets/samples/*.jsonl`, 8 datoteka × 5 primjera = 40 primjera, izvor `manual-seed-v0.1`.
- Proširenje do ~300–500: teacher-generisani primjeri iz semenskih predložaka (po 30–60 po kategoriji: choice, ranking, scoring, yes/no, multicriteria, risk, abstention, confidence), omjer bs:en 75/25, hard negativi i adversarial `abstain` primjeri obavezni (min. 10% skupa).
- Pravilo: primjer bez svih 6 provenance polja (`teacher`, `dataset`, `metoda`, `verzija`, `validacija`, `licenca`) ne ulazi u trening.

## 3. Metrike

Iz `benchmarks/harness.py`: `accuracy` (choice), `ndcg@5` + `mrr` (ranking), `mae_scores` (scoring), `brier` + `ece_10` (kalibracija), `abstention_precision` + `abstention_recall` (abstinencija). Izvještaj uvijek ukupno + `by_lang` (bs/en odvojeno).

## 4. Kriterij uspjeha C-a

C pobjeđuje ako je bolji od A i B na bs dijelu na `accuracy` i `ndcg@5` uz ne-degradiran en (en `accuracy` unutar ±1 bod od B). Ako C ne ispuni oba uslova, pobjednik je bolji od A/B, a joint schema glava se ne uvodi.

## 5. Procjena trajanja na 1×24GB (bf16, LoRA)

| Krak | Vrijeme | Napomena |
|---|---|---|
| A | ~1–2h | samo SFT na seedu |
| B | ~2–4h | adaptacija + glave |
| C | ~4–8h | B + teacher inferenca (clef-flash lokalno, TildeOpen-30B generisanje dominira) |

VRAM: svaki krak staje u 24GB (LoRA + gradient checkpointing + max_seq_length 4096).

## 6. Naredbe

```bash
# Provjera bez GPU-a (radi na CPU, bez downloada):
python3 scripts/pilot.py --arm a --dry-run
python3 scripts/pilot.py --arm b --dry-run
python3 scripts/pilot.py --arm c --dry-run

# Pravi rad na GPU čvoru (tek kad se GPU pojavi):
BH_DECISION_ALLOW_TRAIN=1 python3 scripts/pilot.py --arm a --no-dry-run --confirm
BH_DECISION_ALLOW_TRAIN=1 python3 scripts/pilot.py --arm b --no-dry-run --confirm
BH_DECISION_ALLOW_TRAIN=1 python3 scripts/pilot.py --arm c --no-dry-run --confirm

# Evaluacija nakon svakog kraka:
python3 benchmarks/harness.py --ref datasets/samples/benchmark.jsonl --pred preds/<arm>.jsonl
```

Slurm: `sbatch slurm/pilot.slurm` (uz popunjene TODO particije/račne/vremena).
