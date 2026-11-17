# Sudzuki 4B Cloud — provjereni tehnički profil / Verified technical profile

> Provjereno 2026-11-17 mjerenjem preko `decisio.*` MCP alata (model `sudzuki-4b-cloud`).
> Status: **discovery (DI FAZA 1 nivo)** — NIJE default provider, ne dirati
> `provider-selection.md` dok se ne provjere cijena, licenca i retention.
> / Measured 2026-11-17 via decisio MCP tools. Discovery only — NOT a default.

## Identitet / Identity

- Model: **`sudzuki-4b-cloud`** — vraćen u svakom odgovoru (`model` polje).
- Alati: `decide` (choice/binary/score/risk), `analyze` (risk), `compare`, `rank`.
- Odgovor nosi: `decision + confidence + probs + margin + reasoning + latency_s + request_id`.
- Cijena: **neprovjerena** — ne koristiti kao default dok nije $0 ili odobreno.
  / Pricing unverified — never default until $0 or approved.
- Licenca/težine/retention: **neprovjereno** — tretirati kao hosted (minimalni state).
- Testirano: samo `decide/choice` (20 poziva). `analyze/compare/rank` netestirani.

## Mjerenje / Measurement (held-out v1, 20 stavki, 2026-11-17)

| Stavke | Točno | Napomena |
|---|---|---|
| bs 001–010 | 8/10 | promašaji 002, 006 |
| en 011–012 | 2/2 | 011 tijesno 0.556 vs 0.433 |
| bs 015–020 (scored) | 5/6 | promašaj 016; 015 tie-break 0.4138=0.4138 |
| gibberish 013 / null-ref 014 | — | ne-bodovano (choice ne može apstinirati) |
| **Ukupno scored** | **15/18 (83%)** | bs 13/16, en 2/2 |

Poređenje: Jev Free 14/14 (100%, ključ mrtav), stock Tacit 7/19 (37%),
Ministral SFT 5/19, Tacit-v2 SFT 2/10. Sudzuki je najbolje što trenutno radi.

## Upozorenja / Caveats (mjereno, ne pretpostavljeno)

1. **Stohastičnost:** stavka 001 dala o2 (pogrešno, conf 0.62) u probi pa o1
   (točno, conf 0.80) u batchu — isti ulaz, različit izlaz. Nema bit-za-bit
   reproducibilnosti; svaki benchmark mora imati rerun.
2. **Latencija p50 ~29 s** (raspon 16–49 s, n=21) — ~100× sporije od Jev Free
   (p50 256 ms). Neupotrebljivo za brzu L0 putanju; eskalacijski/adaptive profil
   ili batch-predobrada, nikad interaktivni L0.
3. **Vjerojatnosti nisu degenerirane** (raspon 0.002–0.997, tijesni pozivi postoje)
   — za razliku od Jev 0/1 degeneracije; kalibracija (ECE) još nije izmjerena.
4. Apstinencija: model ne može vratiti abstain kroz choice (013 → "Approve");
   gibberish ulaz i dalje treba `precheck`/poseban noul sloj.

## Sljedeće (uz odobrenje)

- Rerun istih 20 radi varijanse (stohastičnost!); ECE kalibracijska krivulja.
- Provjera cijene/licence/retention → tek onda prijedlog za provider-selection.
- Test `analyze/compare/rank` na istom setu.
