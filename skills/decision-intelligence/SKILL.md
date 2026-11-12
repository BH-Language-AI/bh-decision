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

## Privatnost / Privacy

- Sticky: `language: bs-ijekavica` kad korisnik piše bosanski.
- Ne šalji: kod repozitorija, API ključeve, lične podatke, punu historiju.
- Ako alat timeouta ili provideri padnu — nastavi normalno bez odluke, ne blokiraj zadatak.
