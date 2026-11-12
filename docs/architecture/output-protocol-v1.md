# Izlazni protokol BH-Decision v1.0 — ZAMRZNUTO

Status: zamrznuto, verzija 1.0. Datum: 2026-11-12.
Svaki model porodice (2B/4B/9B) vraća ovaj oblik iz jednog forward passa; kratko obrazloženje je opcioni generativni dodatak, nikad izlaganje privatnog chain-of-thoughta.

## Polja

| Polje | Tip | Obavezno | Dozvoljene vrijednosti / oblik |
|---|---|---|---|
| `decision` | string | da | `choice_id` (id iz ulaznih opcija) \| `yes` \| `no` \| `abstain` |
| `options_ranked` | niz stringova | da za choice/ranking, inače prazan niz | ids iz ulaza, silazno po vjerovatnoći; prazan `[]` za yes/no/abstain |
| `scores` | mapa string→broj | ne (da za scoring) | ključ = id opcije ili naziv skora, vrijednost broj u [0,1] |
| `risk` | objekat | da | `{"level": "low\|medium\|high", "factors": [string, ...]}`; `factors` može biti prazan samo uz `low` |
| `confidence` | broj | da | [0,1], kalibriran temperaturnim skaliranjem |
| `abstention_reason` | string \| null | da (null kad nema abstinencije) | `null` \| `nedovoljno informacija` \| `konfliktna ograničenja` \| `niska pouzdanost` \| `nedozvoljen zahtjev` |
| `rationale_short` | string \| null | ne | 1–2 rečenice na bosanskoj ijekavici; izostaviti (null) kad nije traženo |
| `lang` | string | da | `bs` \| `en` (jezik ulaznog zahtjeva) |
| `model` | string | da | `BH-Decision-2B` \| `BH-Decision-4B` \| `BH-Decision-9B` |
| `version` | string | da | `"1.0"` |

## Pravila

1. `abstain` je legitiman izlaz, ne greška: koristi se kad je pouzdanost ispod praga, kad nedostaju informacije ili kad su ograničenja konfliktna.
2. Zabrana izmišljanja sigurnosti: `confidence` mora biti kalibriran; zabranjeno je vraćati visok `confidence` uz prazne `risk.factors` na rizičnom zadatku.
3. Constraint blokira odluku: pad constraint checka (classification head) prisiljava `decision: abstain` s `abstention_reason: konfliktna ograničenja` ili `nedozvoljen zahtjev`, bez obzira na ostale glave.
4. `decision: choice_id` mora biti jedan od ulaznih id-eva; halucinirani id je nevalidan izlaz.
5. `rationale_short` je uvijek na ijekavici kad postoji, bez obzira na `lang`.

## Primjer

```json
{
  "decision": "id3",
  "options_ranked": ["id3", "id1"],
  "scores": {"id3": 0.71, "id1": 0.29},
  "risk": {"level": "medium", "factors": ["nepotpun ulazni podatak"]},
  "confidence": 0.71,
  "abstention_reason": null,
  "rationale_short": "Treća opcija najbolje zadovoljava zadana ograničenja uz prihvatljiv rizik.",
  "lang": "bs",
  "model": "BH-Decision-9B",
  "version": "1.0"
}
```
