# Specifikacija decision glava BH-Decision — ZAMRZNUTO (FAZA 2)

Status: zamrznuto. Datum: 2026-11-12.
Trupovi: EuroLLM-9B (9.154B) / EuroLLM-1.7B (stvarnih 1.657B, dokumentovati odstupanje). Implementacija vlastita, po Strands Decider principu (Apache 2.0 recept); bez kopiranja koda bez provjere licence. Qwen-bazirani modeli (Clef, Kev) nisu baze — samo baseline/teacher.

## 1. Pointer head (choice / ranking)

- Uloga: izbor jedne opcije ili rangiranje skupa opcija.
- Ulaz: finalni hidden states trupa za state + ugrađene reprezentacije N opcija (N promjenljiv, maskiran padding).
- Izlaz: vektor vjerovatnoća duljine N (softmax nad maskom), `options_ranked` silazno.
- Parametri okvirno: linearna projekcija hidden_dim → hidden_dim/4 + skor vektor; red veličine ~1M (uzor: Strands pointer ~1M + rank-16 LoRA na trupu).
- Loss: cross-entropy nad maskiranim softmaxom (choice); za ranking listwise cross-entropy nad permutacijom ili pairwise hinge kao pomoćni loss.
- Kad se koristi: svaki zadatak s ponuđenim opcijama (choice, ranking, višekriterijski izbor).

## 2. Scoring head (regresija + kalibracija)

- Uloga: kontinuirana ocjena (npr. rizik-skor, kvalitet, vjerovatnoća ishoda) u [0,1].
- Ulaz: pooled hidden state statea (+ opciono reprezentacija cilja).
- Izlaz: skalar u [0,1] (sigmoid), pohranjen u `scores`.
- Parametri okvirno: MLP 2 sloja (hidden_dim → hidden_dim/4 → 1), red veličine ispod 1M.
- Loss: MSE ili binary cross-entropy prema cilju + Brier skor kao metrika kalibracije na validaciji.
- Kad se koristi: scoring zadaci, forecast, rizik-skor kao dopuna `risk.level`.

## 3. Classification head (yes/no + constraint check)

- Uloga: binarna odluka (da/ne) i binarna blokada ograničenja.
- Ulaz: pooled hidden state statea + kodirano pravilo/ograničenje.
- Izlaz: dva logita → `decision: yes | no`; constraint izlaz binaran (prolaz/pad).
- Parametri okvirno: linearna glava (hidden_dim → 2) + mala glava za constraint (hidden_dim → 1); red veličine stotine hiljada.
- Loss: binary cross-entropy po oba izlaza (zasebne težine; constraint loss s većom težinom jer blokira).
- Kad se koristi: yes/no pitanja; constraint check se izvršava prije svake odluke — pad ograničenja blokira odluku (vidi protokol v1.0) bez obzira na ostale glave.

## 4. Ranking head (pairwise / listwise)

- Uloga: učenje poretka kad je nadzor u obliku poređenja, ne apsolutnih ocjena.
- Ulaz: par (ili lista) reprezentacija opcija iz istog statea.
- Izlaz: skor po opciji; poredak izveden sortiranjem.
- Parametri okvirno: dijeli pointer mehaniku i parametre (ista projekcija); bez zasebne velike glave.
- Loss: pairwise Bradley-Terry / hinge loss; listwise softmax cross-entropy kad je dostupna puna permutacija.
- Kad se koristi: preference podaci iz distilacije, ljudske ocjene poretka, reranking.

## 5. Confidence / calibration head (temperatura + abstention)

- Uloga: kalibrirana pouzdanost i odluka o suzdržavanju.
- Ulaz: logit statistike aktivne glave (max logit, margina top-1/top-2, entropija) + pooled state.
- Izlaz: `confidence` u [0,1]; prag ispod kojeg izlaz postaje `abstain`.
- Parametri okvirno: temperaturni skalar po glavi + mala logistička glava (ispod 100K param).
- Loss: kalibracija na held-out setu (temperaturno skaliranje, ECE/Brier minimizacija); prag se bira na validaciji prema ciljanoj pokrivenosti/preciznosti, ne napamet.
- Kad se koristi: uvijek — svaka odluka nosi confidence; niska pouzdanost je legitiman `abstain` (vidi protokol).

## 6. Ablation-alternativa: joint schema head (po uzoru na Cloudflare Clef, Apache 2.0)

- Šta je: mala transformer glava koja čita finalne hidden states, rutira dokaze iz statea na svako pitanje i skorira sve opcije svih pitanja zajedno, sa softmaxom po pitanju. Izvor uzora: `Cloudflare/clef-flash`, `joint_schema_model.py` (proučavanje dozvoljeno, Apache 2.0; trup Qwen se ne preuzima).
- Šta pilot poredi: pojedinačne glave (pointer + scoring + classification, svaka svoj softmax/loss) protiv joint schema glave (jedno zajedničko skoriranje svih pitanja) na istom ijekavskom mini-setu. Metrike: choice accuracy, ranking kvalitet, scoring greška, Brier/ECE, abstention kvalitet, latencija. Uspjeh joint glave = statistički bolji rezultat na višekriterijskim zadacima uz ne-degradiran en; inače ostaju pojedinačne glave.
