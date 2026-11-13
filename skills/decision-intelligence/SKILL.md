---
name: decision-intelligence
description: Structured decision support via BH-Decision MCP tools (classify, route, tool-pick, complexity, risk, rank, score, confidence, escalation). Use when a task needs a calibrated judgment call; skip for trivial or deterministic work.
---

# Decision Intelligence

Pozivaj MCP alate `decision_*` kad trebaš kalibriranu odluku; preskoči ih za trivijalan
ili deterministički posao. / Call `decision_*` MCP tools when you need a calibrated
judgment; skip them for trivial or deterministic work.

## Kada DA / When YES

- Više valjanih sljedećih koraka, nisi siguran koji (klasifikacija, rutiranje).
- Biranje alata/agenta/modela između 2+ kandidata.
- Procjena složenosti ili rizika prije akcije.
- Tvrdiš nešto nesigurno — provjeri `decision_confidence` pa eskaliraj ako je nisko.

## Kada NE / When NO

- Determinističko pravilo postoji (lint, format, postojeći helper) — ne zovi model.
- Već si donio istu odluku u ovoj sesiji — ne ponavljaj poziv.
- Trivijalan upit (čitaj datoteku, odgovori na pitanje) — direktno radi.
- Budžet: najviše ~20 odluka po sesiji; svaki poziv košta latenciju.

## Kako zvati / How to call

1. Minimalni state: samo opis zadatka + kandidati. NIKAD cijeli repo, historiju chata ili tajne.
2. `decision_classify` / `decision_route` / `decision_select_tool` za izbor; `decision_rank` vraća poredak po vjerojatnosti; `decision_score` boduje svaku opciju po rubrici.
3. Gledaj `confidence` i `abstained`: ispod praga ili apstinencija → `decision_should_escalate`, pa sam rasuđuj ili pitaj korisnika. Vjerojatnost NIJE kalibrirano povjerenje u stvarni svijet.
4. `requires_escalation: true` ili visok rizik → ne izvršavaj sam; traži odobrenje.
5. Odluka je savjet, ne dozvola: destruktivne akcije (brisanje, rm, deploy, objave, novac, kredencijali) uvijek prolaze normalna permission pravila.
6. Paralelizam: ako ionako čekaš korisničko odobrenje za rizičnu akciju, `decision_assess_risk` pozovi paralelno s prikazom odobrenja — latencija odluke se ne vidi.

## AnyJev Decision Engine

AnyJev (Apache-2.0, `nokia-applied-research/AnyJev`) pretvara otvorene modele u Jev-stilske
odluke bez treninga: `Decider` (bilo koji lokalni model, nivo L0) i `Tacit` (samodestilirani
`morriszjm/Tacit-{1.7B,2B,4B,8B,9B}`, jedan forward; `adaptive=True` šalje nesigurne na reasoning
uz cap). Vrste: `choice` (max 26 opcija!), `yes_no`, `score` (2–10 nivoa). Svaka odluka nosi
`answer + probs + route` (`one_forward`/`cot`) — vjerojatnost NIJE garancija.

- **Kada AnyJev:** lokalna odluka bez slanja podataka vani; brze L0 rutine (klasifikacija, tool-pick, routing).
- **Decider vs Tacit:** Decider = bilo koji model koji već imaš; Tacit = kalibriraniji jedan-forward, treba Tacit checkpoint.
- **L0 vs Adaptive:** L0 uvijek prvo; Adaptive samo kad je L0 nesiguran (mala margina) i kad sekunde reasoninga vrijede.
- **Kada Jev Free:** primarna hostirana ruta; šalje se samo minimalni state, nikad repo/tajne.
- **Kada Clef-Flash lokalno:** SystemOne fallback kad AnyJev nema modela.
- **Kada eskalacija/abstinencija:** `confidence` ispod praga, `route=cot` bez poboljšanja, ili `abstained` → glavni LLM/korisnik.
- Operativna politika: 1) deterministička pravila prije modela. 2) AnyJev L0 za brze odluke. 3) Jev Free kao primarna hostirana ruta. 4) AnyJev Adaptive samo uz opravdanje. 5) Clef lokalno kao fallback. 6) Složenost glavnom agentu. 7) Bez dokaza → abstiniraj. 8) Probabilnost ≠ istina. 9) Dozvole uvijek važe.
- Status/provjera: `decision_anyjev_status`, `decision_anyjev_test`; ručno: `/decision`,
  `/decision-risk`, `/decision-rank`, `/decision-status` (sve tri prve primaju `provider=<id>` prefiks).
- Ručni primjeri: `/decision-risk obriši staru bazu` → `risk_level=high ... ESCALATE`;
  `/decision-rank trebam alat za pretragu | grep, glob, websearch` → `rank=...`.
  Rank opcije se dijele zarezom (opcija sa zarezom nije podržana).

## Privatnost / Privacy

- Sticky: `language: bs-ijekavica` kad korisnik piše bosanski.
- Ne šalji: kod repozitorija, API ključeve, lične podatke, punu historiju.
- Ako alat timeouta ili provideri padnu — nastavi normalno bez odluke, ne blokiraj zadatak.
