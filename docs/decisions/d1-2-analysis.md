# d1.2 analiza — šta preuzimamo (2026-11-18)

> Izvor: Liquid AI, "d1.2: State-of-the-Art Omnimodal Decision Models" (16.11.2026).
> Preuzeto samo ono što radi bez plaćenih API-ja i bez nove infrastrukture.

## 1. Proper scoring u evaluaciju (PREUZETO, kod)

- d1.2 se rangira i po **kalibraciji** (ECE: ultra 0.8, Jev 1.14 2.7 — naš Jev je 1.13,
  verzija driftuje, pratiti), a Decision Index kažnjava samouvjeren pogrešan odgovor
  više od neodlučnog. Naš held-out je do sad mjerio samo tačnost.
- Preuzeto: `minimal_score` u `scripts/evaluate.py` sad računa i **Brier score**
  (srednja kvadratna greška vjerovatnoće tačnog odgovora) kad predikcija nosi `probs`.
  Test: `tests/test_evaluate.py`. Kalibracija je ionako obavezan cilj treninga —
  sad je mjerimo i na benchmarku, ne samo u trening planu.

## 2. Novi tipovi zadataka → prijedlog za protokol v1.1 (dizajn, NE kod)

- d1.2 dodaje: čitanje vrijednosti (text/number/date), spans (svi navodi vrste),
  box/boxes (lokacija na slici), procjena broja s rasponom, **multi-select choice**.
- Za nas relevantno (bez multimodalnosti, bez novog hardvera):
  - `multi_choice` (više tačnih opcija s pojedinačnim vjerovatnoćama) — direktno
    primjenjivo na naše ranking/multicriteria setove; prijedlog za protokol v1.1.
  - ekstrakcija (text/number/date) + **"not found" umjesto nagađanja** — poklapa se
    s našim `abstention_reason`; kod ekstrakcijskih zadataka apstinencija postaje
    obavezna, ne opciona.
  - box/audio/estimate-range: van opsega (nemamo slike/zvuk) — ne preuzimamo.
- Status: samo prijedlog; protokol v1.0 ostaje zamrznut (FAZA 2 pravilo).

## 3. Metodologija benchmarka (preuzeto kao praksa)

- Held-out splitovi javnih setova za nove zadatke + interni testovi — mi to već
  radimo (heldout-v1 zaključan, leakage 0/20 provjeren). Potvrda smjera, bez akcije.
- Cijene: d1.2 $0.02 / ultra $0.042 po 1M ulaznih tokena — PLAĆENO, ne koristiti;
  endpoint je SystemOne-kompatibilan (`/decisions/v1/systemone`), pa tehnička
  integracija kasnije košta malo — ali `allow_paid=false` ostaje.
- Citiranje: Liquid AI (2026), d1.2 blog — upisati u literaturu kad budemo citirali
  vanjske decision modele.
