# Pilot B smoke — rezultat (2026-11-12, Kaggle T4)

Kernel: admiragic/bh-decision-pilot-b-smoke-eurollm-1-7b-lora (v13, COMPLETE).
Model: utter-project/EuroLLM-1.7B + LoRA r16/a32 (svi attn+mlp), fp16, 100 koraka.

## Loss (40 seed primjera, 50 epoha — memorisanje, ne generalizacija)

| step | loss |
|---|---|
| 10 | 1.725 |
| 20 | 0.783 |
| 50 | 0.090 |
| 100 | 0.025 |

## Generacije (3 probe, skraćeno)

Model reprodukuje protokol v1.0 kao JSON s ijekavicom (`decision`, `confidence`,
`abstention_reason: "nedovoljno informacija"`, `rationale_short` na bosanskom).
Primjer: `{"decision": "abstain", "confidence": 0.3, ...}` za zahtjev bez priloga.

## Verdict

PIPELINE RADI: EuroLLM-1.7B se učitava, LoRA trenira na T4, loss pada 1.7→0.02,
izlaz je validan protokolski JSON na ijekavici. Ovo NIJE dokaz kvaliteta —
40 primjera × 50 epoha = čista memorizacija. Pravi pilot A/B/C (300–500
primjera, eval harnessom, 1–8h) ostaje sljedeći korak čim se pripremi veći
bosanski set. Adapter se ne objavljuje (smoke, nevalidiran).
