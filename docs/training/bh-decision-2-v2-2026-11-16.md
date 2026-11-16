# BH-Decision-2 mix v2 run (2026-11-16/17, Kaggle T4, QLoRA fp16)

> Tacit-4B + QLoRA (r16, 3 epohe) na `train-v2.jsonl` (4989, samo JSON ciljevi).
> Kernel: `kaggle/bh2-mixv2/`. Sirove generacije na Kaggle outputu + `/tmp` (gitignore).

## Rezultat

- `val_loss: 0.124` (train 4490 / val 499) — lijep broj bez vrijednosti (memorisanje šablona).
- Format validan: **10/20 (0.5)** — pad i od v1 adaptera (0.75) i od stocka.
  Drugih 10: Python-dict sintaksa s jednostrukim navodnicima ili odsijecanje na 256 tokena.
- Held-out: **2/10 (20%)**; model odgovara **o2 na 19/20** (jedini izuzetak: gibberish stavka → o3).
- Poređenje: stock Tacit 7/19 (37%) > v1 adapter 4/15 > v2 adapter 2/10.

## Dijagnoza

1. **o2-default je strukturni, ne brojački:** o1=o2=1559 u miksu, a model svejedno
   kolabira na o2. Subsample praga ne pomaže — prior je u poziciji/leksici šablona
   ("o2" je u šablonima najčešće "razumna sredina"), pa ga SFT samo pojačava.
2. **Format se kvari čišćenjem, ne popravlja:** uklanjanje think-tragova nije vratilo
   JSON disciplinu — backboneov pretraining stil (Python-dict) cure kad SFT oslabi.
3. Stock (7/19) i dalje najbolji lokalni rezultat na held-outu — obje SFT linije
   (Ministral 5/19, Tacit-v1 4/15, Tacit-v2 2/10) kvare umjesto da popravljaju.

## Zaključak

- **Linija 2 SFT se pauzira**, isto kao Linija 1: template-SFT plafon je dokazan
  na dva backbona. Dalje skaliranje šablona je bacanje GPU vremena.
- Preostalo (redom isplativosti): (a) human 10x s plauzibilnim distraktorima,
  (b) prihvatiti stock Tacit 7/19 kao lokalni baseline i fokus na DI inferenciju,
  (c) LUMI bf16 rerun mixa v2 radi potvrde da pad nije T4/QLoRA artefakt —
  nisk prioritet, ne mijenja odluku.
