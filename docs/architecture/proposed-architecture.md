# Predložena arhitektura BH-Decision — FAZA 1 (nacrt za FAZU 2)

Status: prijedlog, nije zaključano. Svaka tvrdnja o prednosti mora se dokazati pilotom iz `docs/decisions/phase-1-recommendation.md`.
Datum: 2026-11-12.

## 1. Identitet porodice

Tri veličine, jedan identitet: zajednički format podataka, zajedničke izlazne sheme, zajednički benchmark. Ciljane veličine su stvarni broj parametara — odstupanja se dokumentuju (npr. EuroLLM-1.7B = stvarnih 1.657B total / 1.133B non-emb.).

## 2. Pristupi A / B / C — poređenje

| Pristup | Opis | Kvalitet | Rizik | Licenca | GPU/memorija | Očekivana prednost |
|---|---|---|---|---|---|---|
| A. Open decision + bs FT | Strands 2B / Kev / d1 + ijekavski FT | brz start, dokazan decision kvalitet | bs slab (EN-trup), d1 prihodni prag 10M | A: Apache 2.0 čisto; d1: LFM prag | najmanji (LoRA na 1×24GB za 2B) | najbrži pilot, ali jezički plafon |
| B. EU foundation + adaptacija + decision | EuroLLM-9B/1.7B + bs adaptacija + decision heads | najbolji bs potencijal (hr transfer + Tilde teacher) | 4k kontekst EuroLLM-a; nema 4B baze; skuplji trening | Apache 2.0 čisto | LoRA 1×24–48GB; full FT 9B 1–2×80GB | jedini put do ijekavskog prioriteta |
| C. Hibrid | EU trup + Strands-inspirisane glave + bs trening + distilacija iz većih decision modela + kalibracija | najveći strop ako distilacija uspije | najsloženiji; pravni rizik teacher-a (Jev ToS, Llama klauzule); redoslijed 9B→4B→2B nedokazan | Apache 2.0 ako teacheri čisti | kao B + teacher inferencija | preporučen, ali NE automatski najbolji — dokazati pilotom |

Hibrid se ne proglašava pobjednikom unaprijed. Pilot mora moći opovrgnuti C u korist A ili B.

## 3. Decision glave (vlastita implementacija, inspiracija Strands receptom — ne kopija koda bez provjere licence)

- Zajednički trunk (EU foundation) → odvojene glave: pointer head (choice/ranking preko maskiranog softmaxa nad opcijama), scoring head (regresija + kalibracija), classification head (yes/no, constraint check), ranking head (pairwise/listwise, dijeli pointer mehaniku), confidence/calibration head (temperatura + pouzdanost, abstention prag).
- Pointer mehanika preuzima princip iz Strands Decidera (mala glava ~1M param + LoRA na trupu) jer je jedini pristup s punim otvorenim receptom; implementacija vlastita nad EU trupom. Alternativa za ablacija-test: joint schema head po uzoru na Clef (mala transformer glava koja zajednički skorira sve opcije svih pitanja odjednom, softmax po pitanju) — pilot mjeri da li zajedničko skoriranje tuče pojedinačne glave na višekriterijskim zadacima. Izvor uzora: https://huggingface.co/Cloudflare/clef-flash (`joint_schema_model.py`, Apache 2.0 — proučavanje dozvoljeno, trup Qwen se ne preuzima).
- Generativni JSON vs strukturirane glave: generativni JSON je fleksibilan za obrazloženja, ali netipiziran, sporiji i sklon halucinaciji sheme; direktne glave daju jedan forward pass, tipiziran izlaz i mjerljivu kalibraciju. Prijedlog: glave kao primarni izlaz (kalibriran, mašinski provjerljiv), kratko obrazloženje kao opcioni generativni dodatak — nikad izlaganje privatnog chain-of-thoughta.

## 4. Zajednički izlazni protokol (nacrt, v0.1)

```json
{"decision": "choice_id | yes | no | abstain",
 "options_ranked": ["id3", "id1"],
 "scores": {"id1": 0.0},
 "risk": {"level": "low|medium|high", "factors": ["..."]},
 "confidence": 0.0,
 "abstention_reason": "nedovoljno informacija | ... | null",
 "rationale_short": "jedna-dvije rečenice na ijekavici",
 "lang": "bs|en", "model": "BH-Decision-2B|4B|9B", "version": "0.x"}
```

Pravila: niska pouzdanost i `abstain` su legitimni izlazi; model ne smije izmišljati sigurnost; constraint check je binaran i blokira odluku.

## 5. Distilacija (vlastita metodologija, porijeklo obavezno)

Tehnike: teacher-generated primjeri, soft-label, preference/pairwise ranking, score distilacija, kalibracijski trening, hard negativi, adversarial primjeri, disagreement-based selekcija. Svaki primjer čuva: teacher, dataset, metodu, verziju, validaciju, licencu. Teacher nije izvor istine — provjera kroz pravila, testove, izvore i ljudsku evaluaciju.
Učitelji: veći decision modeli (Strands 12B/26B-A4B, clef-flash 9B — svi Apache 2.0, čisto) kao decision teacheri; TildeOpen-30B (CC-BY-4.0, atribucija) kao jezički teacher i generator ijekavskih podataka. Jev i Llama-izvedeni reward modeli NE kao teacheri bez pravne provjere. Redoslijed 9B→4B→2B tretirati kao hipotezu: testirati i 2B-direktno i 4B-iz-9B pruning/distilaciju.

## 6. Jezička strategija

Samo bosanska ijekavica (apsolutni prioritet) + engleski (tehnički kontekst). Bez širenja na druge jezike. Trening pokriva: prirodnu ijekavicu, padeže/sintaksu, lokalnu terminologiju, negaciju/dvosmislenost/složene rečenice, administrativni/pravni/poslovni/tehnički/svakodnevni registar — bez engleskog kao posrednika.
Omjer bs:en: eksperimentalno, ne fiksno. Polazna hipoteza za pilot: 70–80% bs / 20–30% en (po tokenima), s ablacijama 60/40 i 85/15; pobjednika bira ijekavski benchmark, ne dogovor.

## 7. Šta FAZA 2 mora isporučiti

Arhitekturu zamrznuti tek nakon pilota: izbor trupa po tieru, dimenzije glava, protokol v1.0, plan distilacije, trening plan s VRAM/GPU-sat procjenama (2B LoRA 1×24GB; 9B LoRA 1×24–48GB, full 1–2×80GB; LUMI primaran za veće poslove; bez skupih jobova bez plana i odobrenja).
