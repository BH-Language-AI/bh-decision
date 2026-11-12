# FAZA 1 — Preporuka i odluke za odobrenje

Datum: 2026-11-12. Status: čeka odobrenje za FAZU 2. Kontakt: xnetba@gmail.com.

## 1. Provjera organizacija (potvrđeno)

- GitHub org BH-Language-AI postoji: https://github.com/BH-Language-AI (5 javnih repoa, nijedan nije BH-Decision).
- HF org postoji: https://huggingface.co/BH-Language-AI (6 modela, 3 kolekcije: bh-speech, agentmujo-llms, bh-llm-basic).
- BH-Decision repo (https://github.com/BH-Language-AI/bh-decision → 404) i kolekcija (404) ne postoje — naziv slobodan, nema duplikata.

## 2. Preporučene baze po veličini (uz dokumentovana odstupanja)

- 9B → EuroLLM-9B (stvarnih 9.154B; Apache 2.0; potvrđen hr). Rezerva: Apertus-8B.
- 2B → EuroLLM-1.7B (stvarnih 1.657B; Apache 2.0; potvrđen hr) + Salamandra-2B kao ablacija.
- 4B → nema evropske 4B baze: vlastiti 4B distilacijom/pruningom iz EuroLLM-9B uz TildeOpen-30B učitelja, ili preskakanje tiera (odluka nakon pilota).
- Učitelj jezika: TildeOpen-30b (CC-BY-4.0, eksplicitan bs/hr/sr/cnr). Decision teacher: Strands 12B/26B-A4B (Apache 2.0).
- Isključeno: Pharia-1 (nekomercijalno), Qwen/američki trupovi kao finalne baze (Clef je Qwen-baziran pa je baseline/teacher, ne baza), Jev kao teacher bez ToS provjere, Llama-izvedeni reward modeli (zabrana distilacije).

## 3. Preporučeni pristup: C (hibrid) kao hipoteza, ne kao dogma

EU trup + vlastite decision glave po Strands principu + bs trening + distilacija iz čistih teachera + kalibracija. Pilot mora moći pobijediti A ili B nad C.

## 4. Prvi pilot eksperiment (dokaz koji pristup radi za bosanski)

Cilj: na istom ijekavskom mini-setu (~300–500 primjera: choice, yes/no, scoring, ranking, risk, abstention; pola ijekavica, dio engleski) uporediti:
- A: Strands-2B + LoRA bs FT (1×24GB, sati — ne dani);
- B: EuroLLM-1.7B + bs adaptacija + scoring/pointer glava;
- C: EuroLLM-1.7B + Strands-inspirisane glave + distilacija iz Strands-12B + TildeOpen-30B generisani ijekavski primjeri.
Metrike: choice accuracy, ranking kvalitet, scoring greška, kalibracija (Brier/ECE), abstention kvalitet, robustness (parafraza + redoslijed opcija), konzistentnost bs↔en — prikazano po jeziku i zadatku, ne jedna ocjena. Obavezni baselineovi u pilotu: clef-flash 9B (Apache 2.0, Jev-kompatibilan — direktno mjerljiv protiv naših modela) i, ako budžet dozvoli, Jev hosted. Omjer-ablacija: 70/30 vs 85/15 bs/en. Uspjeh C-a = statistički bolji od A i B na bs-ijekavskom dijelu uz ne-degradiran en; inače se ide s pobjednikom.
Trošak: samo 1×24GB klasa, bez LUMI jobova; bez skupih treninga.
- Eval-instrumentacija po uzoru na clef-playground (https://github.com/JordanDalton/clef-playground): side-by-side poređenje modela s latencijom i cijenom po pozivu — ali BEZ kopiranja koda jer repo nema vidljivu licencu (samo obrazac, vlastita implementacija). Bosanski pandan `TurkishDecisionBenchmark` Spacea planirati u FAZI 3.

## 5. Otvorena pitanja i rizici

- Nijedan decision vendor ne dokazuje bs/hr/sr — transfer hr→bs ijekavica traži mjerenje.
- EuroLLM kontekst 4k može ograničiti višekriterijske zadatke (Apertus 65k rezerva).
- LFM prag 10M USD i Llama zabrana distilacije su pravne zamke — d1 samo za poređenje.
- 4B praznina: distill/prune vs preskakanje.
- TildeOpen je base-only (bez instructa) — teacher/generator, ne baza.

## 6. Traženo odobrenje za FAZU 2

Arhitektura glava + protokol v1.0 + plan distilacije + trening plan. Bez zamrzavanja baza prije pilot rezultata. Bez kreiranja GH repoa / HF kolekcije i bez GPU troškova do odobrenja.
