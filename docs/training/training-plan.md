# Trening plan BH-Decision — FAZA 2

Status: plan, bez pokretanja skupih jobova u ovoj fazi. Datum: 2026-11-12.

## 1. Redoslijed faza

1. Jezička adaptacija — EuroLLM trupovi (9B; 1.7B) na ijekavskom korpusu (prirodna ijekavica, padeži/sintaksa, lokalna terminologija, registri: administrativni, pravni, poslovni, tehnički, svakodnevni).
2. Decision trening — zamrznute glave iz `docs/architecture/decision-heads.md` + protokol v1.0, na pilot setu (~300–500 primjera) pa na punom distilacijskom skupu.
3. Kalibracija — temperaturno skaliranje + prag abstinencije na held-out setu.

## 2. LoRA prvo

- Početne vrijednosti: r=16, alpha=32, dropout=0.05, ciljani moduli pažnje i MLP projekcije.
- Full fine-tune samo ako LoRA ne dosegne cilj na ijekavskom benchmarku (definisano u pilotu, ne napamet).

## 3. Jezički omjer

- Početna tačka (po tokenima): bs:en 75/25.
- Obavezne ablacije: 60/40 i 85/15; pobjednika bira ijekavski benchmark.

## 4. Procjene resursa (okvirno, bf16)

| Model | LoRA | Full FT | Skladište (checkpoint + podaci) |
|---|---|---|---|
| 2B (1.7B) | 1×24GB, sati | 1×40–80GB, ~1 dan | desetine GB |
| 9B | 1×24–48GB, sati–dani | 1–2×80GB, dani | stotine GB |

4B tier nema vlastiti trening od nule: nastaje distilacijom/pruningom iz 9B uz TildeOpen-30B učitelja, ili se preskače (odluka nakon pilota).

## 5. Infrastruktura

- LUMI primaran za veće poslove (TildeOpen-30B je treniran na LUMI-ju; provjeriti pristup prije planiranja).
- Slurm za raspoređivanje; checkpointing svakih N koraka + na prekid; nastavak od zadnjeg checkpointa.
- Reproducibilnost: fiksiran seed, zabilježene verzije koda/modela/biblioteka, hash trening podataka uz svaki run.
- Pravilo: bez skupih jobova (full 9B, teacher inferencija u velikom obimu) bez pisanog plana i odobrenja.
