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

## Rerun (2026-11-17, istih 20 stavki)

- Ukupno scored: **14/18 (78%)** — run 1 bio 15/18 (83%).
- Razlike: 001 se popravila (o2→o1), 015 se pokvarila (o2→o3, tie-break 0.41=0.41
  pa 0.40 o3). Slaganje run1-vs-rerun: **18/20 (90%)** — stohastičnost postoji,
  ali je ograničena na tijesne pozive.
- Latencija reruna p50 **~5 s** (raspon 2–14 s) umjesto ~29 s — model je bio
  topao ili je opterećenje palo; L0 priča i dalje ne stoji (Jev 256 ms),
  ali 5 s mijenja računicu za batch/adaptive upotrebu.
- Cijena: javno neprovjerljiva (nema tragova `sudzuki-4b-cloud` modelu na webu —
  vjerovatno interni harness model). Status ostaje: **nikad default** dok se
  cijena/licenca ne potvrde pisanim putem.

## Kalibracija (2026-11-18, oba runa, n=36 bodovanih)

| Bin povjerenja | n | Tačnost | Prosj. conf |
|---|---|---|---|
| 0.2–0.4 | 1 | 0.00 | 0.40 |
| 0.4–0.6 | 3 | 1.00 | 0.50 |
| 0.6–0.8 | 12 | 0.50 | 0.70 |
| 0.8–1.0 | 20 | 1.00 | 0.93 |

**ECE ≈ 0.16 (16 poena)** — debelo iznad d1.2-ultra (0.8) i Jev 1.14 (2.7) iz
d1.2 članka (drugi benchmarkovi, nije direktno uporedivo, ali red veličine je jasan).
Obrazac: visoki bin savršen (20/20), srednji pre-samouvjeren (0.50 vs 0.70).
Zaključak za pragove: odluke s conf < 0.8 šalji na eskalaciju/ljudsku provjeru —
prag 0.80 iz SKILL.md-a ovim dobija empirijsku potvrdu. Uzorak mali (n=36).

## Ostali alati (2026-11-18)

- `analyze` (kašnjenje plate): risk **high** (0.69) — razumno.
- `compare` (3 opcije): pisani rok isplate, 0.99 — razumno.
- `rank` na cijelom held-outu (18 bodovanih): **17/18** — jedina greška 007.
  Ranija n=1 proba ("Razbiti zid sam" prvi) bila je artefakt moje greške: opcije
  bez konteksta situacije. Kad opcije nose puni tekst, rank radi. Pouka za skill:
  nikad kratke opcije bez statea.
