# BH-Decision-2 prvi run (2026-11-16, LUMI bf16, job 23781616, 109 min)

> Tacit-4B backbone + LoRA na bh-decision-2 miksu (8474). Baseline stock Tacit: 7/19 (37%).

## Rezultat

- `val_loss: 0.80`, format **0.75** (pad!), held-out **4/15 (27%)**.

## Dijagnoza (iz generacija)

1. **Format se raspao na miješanom miksu:** `<think>` tragovi (iz thinking seta) cure u
   izlaz umjesto JSON-a; agentic tragovi (iz bosnian-core) proizvode parrotiranje
   ("ne diraj ništa" × N). Slobodni tekst uči slobodni tekst — očekivano.
2. **o2-default i dalje dominira** gdje je JSON validan — prior miks/šablona jači od human signala.
3. Stock Tacit (37%) i dalje najbolji — SFT zasad samo kvari.

## Sljedeće (mix v2)

- Thinking tragove svesti na JSON-oblik (bez `<think>` bloka) ili izdvojiti u poseban reasoning-set.
- Iz bosnian-core uzeti samo ne-agentske, čiste instrukcije (bez loop/trace sadržaja).
- Povećati udio human + heldout-sličnih stavki; o2-težinu srezati subsampleom.
