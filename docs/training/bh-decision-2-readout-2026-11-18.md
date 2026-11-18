# Readout presuda (2026-11-18, lokalni CPU, AnyJev Tacit one_forward)

> Stock vs bh2-v4 vs bh2-v5 — svi kroz ISTI joint-head readout, neutralna pitanja
> (bs "Koji je najbolji odgovor?" / en "Which is the best option?").
> Sirovo: `datasets/selfdistill/readout-v45.jsonl`. Skripta: `scripts/readout_eval.py`
> (v1 je imala bug tekst-vs-ID; ispravljeno, brojevi preračunati iz odgovora).

## Rezultat

| Model | Tačno (readout) | Tačno (generacija, staro) |
|---|---|---|
| stock Tacit-4B | **16/19 (84%)** | 7/19 (37%) |
| bh2-v4 (mix v4) | **15/19 (79%)** | 3/16 (19%) |
| bh2-v5 (mix v5) | **15/19 (79%)** | 3/19 (16%) |

## Presuda

1. **Readout je 2× bolji od generacije** (16/19 vs 7/19 na istom backboneu).
   Sva generacijska mjerenja v1–v5 podcjenjuju model — proizvodni put je
   readout (strukturirane vjerovatnoće, bez trailing garbagea po konstrukciji),
   nikad slobodna generacija.
2. **SFT jedva dira backbone** (16→15, unutar šuma ±1): zaključak "SFT kvari
   rasuđivanje" je bio artefakt generacijskog interfejsa. Adapter čuva ~sve.
3. **v4 je najbolji adapter** (15/19 + format 0.85 u generaciji) → kandidat za v0.2
   uz readout-evaluaciju kao službenu metriku.
4. Proizvodni prag: format 1.0 (readout ga daje strukturom) + held-out ≥ stocka.
   v4 je na pragu (15 vs 16 — jedan item). Sljedeći korak: v0.2-rc objava s
   readout brojkama, bez tvrdnje da tuče stock.
