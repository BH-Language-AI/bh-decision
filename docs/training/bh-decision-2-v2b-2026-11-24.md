# BH-Decision-2-2B v1 (Qwen3-1.7B + recept A, LUMI job 23993464)

> Prvi 2B: stock 7/19 (o2-default) → **v2b 13/19 (o1 11/o2 7/o3 1)**.
> Recept A (r32/rsLoRA/cosine/1024, 4 epohe, mix v10) se prenosi na mali model.

## Rezultat (readout q1, held-out 20/19)

| Model | Tačno | Distribucija |
|---|---|---|
| stock Qwen3-1.7B | 7/19 (37%) | o2 13 (default) |
| **bh2-v2b** | **13/19 (68%)** | o1 11 / o2 7 / o3 1 (bez defaulta) |

## Dijagnoza

- Recept A rješava i mali model: prior slomljen, distribucija zdrava.
- Generacija (strogo 1/20, tolerantno 3/19) i dalje slaba — proizvod je readout,
  kao i kod 4B.
- Sljedeće: objava kao 2B linija + 9B run istim receptom (EuroLLM-9B).

## Objava (25.11.2026)

- Adapter povučen sa LUMI-ja (`bh2-2b-v1/out/adapter`, sha256 match),
  objavljen kao [`BH-Language-AI/bh-decision-2-2b`](https://huggingface.co/BH-Language-AI/bh-decision-2-2b)
  (adapter + config + kartica). Smoke s HF-a OK (učitavanje + validan JSON).
