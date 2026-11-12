# Metodologija distilacije BH-Decision

Status: plan FAZE 2. Datum: 2026-11-12.
Načelo: teacher nije izvor istine — svaki teacher primjer prolazi provjeru kroz pravila, testove, izvore i ljudsku evaluaciju prije ulaska u trening.

## 1. Teacheri

- Decision teacheri: Strands 12B / 26B-A4B i clef-flash 9B (svi Apache 2.0 — pravno čisto za distilaciju).
- Jezički teacher: TildeOpen-30B (CC-BY-4.0, obavezna atribucija) — generator ijekavskih podataka i jezičkih ocjena. Base-only model, služi kao teacher/generator, ne kao baza.
- Zabranjeni teacheri: Jev (ToS navodi zabranu distilacije, potrebna pravna provjera) i Llama-izvedeni modeli (zabrana korištenja outputa za trening drugog LLM-a, MAU klauzula). d1 se koristi samo za poređenje, ne kao teacher bez pravnog mišljenja (prihodni prag 10M USD).

## 2. Tehnike (redoslijed primjene)

1. Teacher-generated primjeri — teacher generiše ijekavske decision zadatke (choice, yes/no, scoring, ranking, risk, abstention) iz semenskih predložaka.
2. Soft-label distilacija — učenje na teacher distribucijama (KL divergencija), ne samo na tvrdim labelama.
3. Preference / pairwise distilacija — teacher rangira parove odgovora (Bradley-Terry loss) za ranking head.
4. Score distilacija — teacher skorovi kao regresijski ciljevi za scoring head.
5. Kalibracijski trening — teacher confidence + temperaturno skaliranje na held-out setu (cilj: Brier/ECE).
6. Hard negativi — namjerno slične pogrešne opcije (parafraze tačnog, zamjena redoslijeda) za robustness.
7. Adversarial primjeri — dvosmisleni, kontradiktorni i nepotpuni ulazi koji moraju završiti u `abstain`.
8. Disagreement-selekcija — zadržavaju se primjeri gdje se teacheri međusobno ne slažu ili gdje je teacher nesiguran; služe za kalibraciju i ljudsku reviziju, ne za slepo učenje.

## 3. Provenance — obavezna polja svakog primjera

Svaki primjer u distilacijskom skupu nosi: `teacher` (naziv + verzija checkpointa), `dataset` (izvor/predložak), `metoda` (jedna od 8 tehnika iznad), `verzija` (verzija generacijske skripte), `validacija` (pravilo/test/ljudska ocjena + ishod), `licenca` (licenca teacher outputa i izvornog podatka). Primjer bez svih šest polja ne ulazi u trening.

## 4. Redoslijed veličina — hipoteza, ne dogma

Polazna hipoteza: 9B → 4B → 2B (kaskadna distilacija). Obavezno testirati i direktnu distilaciju (teacher → 2B) i nastanak 4B pruningom/distilacijom iz 9B. Bira ijekavski benchmark, ne dogovor; 4B tier se preskače ako pilot ne pokaže dobit nad 2B.
