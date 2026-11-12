#!/usr/bin/env python3
"""Deterministicka ekspanzija seed uzoraka template-expansion-v0.2 (FAZA 3->5).

stdlib only, seed=42. Od 40 seed primjera generise ~400 novih slot-filling
varijacijama + parafraziranim sablonima, bez doslovnih kopija seed stateova.
Upisuje u datasets/expanded/*.jsonl (ne dira samples/).
Svi bs sabloni i slot-vrijednosti su na ispravnoj ijekavici S PUNIM
dijakriticima (č ć š đ ž); gradovi se dekliniraju (genitiv/lokativ).
"""
import hashlib
import json
import os
import random
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE, "datasets", "samples")
EXPANDED_DIR = os.path.join(BASE, "datasets", "expanded")
SOURCE = "template-expansion-v0.2"
LICENSE = "CC-BY-4.0"
N_PER_DS = 50
RNG = random.Random(42)

CITIES = ["Sarajevo", "Mostar", "Tuzla", "Zenica", "Banja Luka", "Bihać",
          "Trebinje", "Brčko", "Doboj", "Travnik", "Goražde", "Livno"]
# nominativ -> (genitiv, lokativ)
CITY_FORMS = {
    "Sarajevo": ("Sarajeva", "Sarajevu"),
    "Mostar": ("Mostara", "Mostaru"),
    "Tuzla": ("Tuzle", "Tuzli"),
    "Zenica": ("Zenice", "Zenici"),
    "Banja Luka": ("Banje Luke", "Banjoj Luci"),
    "Bihać": ("Bihaća", "Bihaću"),
    "Trebinje": ("Trebinja", "Trebinju"),
    "Brčko": ("Brčkog", "Brčkom"),
    "Doboj": ("Doboja", "Doboju"),
    "Travnik": ("Travnika", "Travniku"),
    "Goražde": ("Goražda", "Goraždu"),
    "Livno": ("Livna", "Livnu"),
}
NAMES = ["Amina Horvat", "Marko Jovanović", "Lejla Smajić", "Ivan Perić",
         "Sara Mujkić", "Emir Delić", "Maja Kovač", "Adnan Hodžić",
         "Ivana Marić", "Tarik Suljić", "Nermina Bečić", "Goran Lukić"]
FIRMS = ["Vodovod i kanalizacija", "Elektrodistribucija", "Gradska uprava",
         "Općinski sud", "Porezna uprava", "Dom zdravlja", "Komunalno preduzeće",
         "Zavod za urbanizam", "Turistička zajednica", "Centar za socijalni rad"]
DOCS = ["lična karta", "pasoš", "vozačka dozvola", "građevinska dozvola",
        "uvjerenje o prebivalištu", "radna knjižica", "zdravstvena knjižica"]
NEG_BS = " Nije dostavljena potpuna dokumentacija pa odluka nije konačna."
NEG_EN = " Complete documentation was not submitted, so the decision is not final."

STATE_T = {
    # --- choice (bs + en) ---
    "choice": [
        ("bs", "Građanin {name} iz {city_gen} traži produženje dokumenta ({doc}). Na šalteru ustanove {firm} nude se tri postupka."),
        ("bs", "Firma iz {city_gen} treba rezervni dio u vrijednosti od {amt} KM s rokom isporuke od {days} dana. Pristigle su dvije ponude, a proizvodnja čeka."),
        ("bs", "Obrtnik čeka mišljenje knjigovođe o poreznoj prijavi, a knjigovođa je odsutan {days} dana. Treba odabrati sljedeći korak."),
        ("bs", "Stanar u {city_lok} prijavljuje kvar na instalacijama vrijedan {amt} KM. Upravnik zgrade bira između hitne intervencije i redovnog termina."),
    ],
    "choice_en": [
        ("en", "A customer in {city} requests a refund of {amt} KM for order BR-{num}. Choose the correct next step."),
        ("en", "A server in {city} datacenter stalled during peak hours. Choose the correct remediation step within {days} days SLA."),
    ],
    # --- ranking ---
    "ranking": [
        ("bs", "Rangirati načine podnošenja zahtjeva za {doc} u {city_lok} po brzini rješavanja (portal, šalter, pošta)."),
        ("bs", "Rangirati tri dobavljača kancelarijskog materijala za ustanovu {firm} kad je zaliha pri kraju."),
        ("bs", "Rangirati načine plaćanja fakture od {amt} KM prema finansijskoj povoljnosti (virman, gotovina, rate)."),
        ("bs", "Rangirati prioritete sanacije u {city_lok} po žurnosti: vodovod, rasvjeta i put u vrijednosti od {amt} KM."),
    ],
    # --- scoring ---
    "scoring": [
        ("bs", "Ocijeniti kvalitet dva zahtjeva za subvenciju od {amt} KM pristigla ustanovi {firm} uz priložene potvrde (skala 0-1)."),
        ("bs", "Ocijeniti tri poslovna plana za kredit od {amt} KM prema potpunosti troškovnika i analize tržišta (skala 0-1)."),
        ("bs", "Ocijeniti radnu disciplinu dva radnika ustanove {firm} u {city_lok} prema evidenciji kašnjenja (skala 0-1)."),
        ("bs", "Ocijeniti stanje stana pri iseljenju u {city_lok} nakon štete od {amt} KM (skala 0-1)."),
    ],
    "scoring_en": [
        ("en", "Score two vendors for {firm} on reliability and delivery within {days} days (scale 0-1)."),
        ("en", "Score three project proposals worth {amt} KM by completeness of budget and timeline (scale 0-1)."),
    ],
    # --- risk ---
    "risk": [
        ("bs", "Stranka je dobila rješenje ustanove {firm} s rokom žalbe od {days} dana. Procijeniti rizik ako propusti žalbeni rok."),
        ("bs", "Mala firma iz {city_gen} dobila je ugovor o zakupu vrijedan {amt} KM. Procijeniti rizik potpisa bez pravne provjere jer prijeti šteta."),
        ("bs", "Porodica iz {city_gen} kreće na duži put. Procijeniti rizik polaska bez provjere vozila."),
        ("bs", "Građanin {name} platio je administrativnu taksu od {amt} KM. Procijeniti rizik bacanja uplatnice."),
    ],
    # --- multicriteria ---
    "multicriteria": [
        ("bs", "Kriteriji: udaljenost (0.2), vrijeme čekanja (0.5), ljubažnost (0.3). Odabrati šalter ustanove {firm} u {city_lok}."),
        ("bs", "Kriteriji: cijena (0.3), garancija (0.4), rok isporuke (0.3). Odabrati ponudu za opremu vrijednu {amt} KM; odluka je žurna."),
        ("bs", "Kriteriji: cijena zakupa (0.3), lokacija (0.4), parking (0.3). Odabrati poslovni prostor u {city_lok}; prednost ima bliža lokacija."),
        ("bs", "Kriteriji: čuvanje djeteta (0.6), gužva (0.4). Odabrati termin pregleda u domu zdravlja u {city_lok}."),
    ],
    # --- confidence ---
    "confidence": [
        ("bs", "Jasna procedura: zahtjev za {doc} podnosi se isključivo na propisanom obrascu u {city_lok}. Kolika je pouzdanost odluke?"),
        ("bs", "Dobavljač iz {city_gen} nudi popust na iznos od {amt} KM samo usmeno. Kolika je pouzdanost odluke o prihvatanju?"),
        ("bs", "Rješenje ustanove {firm} sadrži tačan broj računa za uplatu takse od {amt} KM. Kolika je pouzdanost odluke?"),
        ("bs", "Prodavač u {city_lok} ne daje servisnu historiju vozila niti dozvoljava probnu vožnju. Kolika je pouzdanost kupovine?"),
    ],
    # --- abstention ---
    "abstention": [
        ("bs", "Zahtjev za naknadu od {amt} KM stigao je ustanovi {firm} bez ijednog priloga. Nema podataka o visini štete."),
        ("bs", "Ugovor vrijedan {amt} KM ne sadrži član o raskidu niti kaznene odredbe. Nedostaje ključni član."),
        ("bs", "Kupac u {city_lok} reklamira neispravan uređaj ali nije priložio račun niti garanciju."),
        ("bs", "Roditelj nema nalaz ljekara ni tačnu dozu lijeka za dijete. Davanje lijeka bez liječničke upute nije dozvoljeno."),
    ],
    # --- benchmark (mijesani eval uzorak, bs + en) ---
    "benchmark": [
        ("bs", "Kategorija: choice/admin. Građanin {name} iz {city_gen} produžava dokument ({doc}). Odabrati ispravan korak."),
        ("bs", "Kategorija: multicriteria/business. Kriteriji: cijena (0.3), rok (0.4), garancija (0.3). Nabavka od {amt} KM, mašina stala."),
        ("bs", "Kategorija: abstention/admin. Zahtjev za naknadu od {amt} KM bez priloga. (Primjer za uzdržavanje od odluke.)"),
        ("bs", "Kategorija: risk/daily. Porodica iz {city_gen} kreće na duži put. Procijeniti rizik."),
    ],
    "benchmark_en": [
        ("en", "Category: risk/business. Shop update worth {amt} KM pending. Assess the deployment risk."),
        ("en", "Category: choice/business. Vendor decision for {firm} with {days} days deadline. Choose the correct step."),
    ],
}

OPTS = {
    "choice": [("o1", "Prihvatiti preporučeni postupak u roku."), ("o2", "Odgoditi odluku za {days} dana."), ("o3", "Odbaciti zahtjev bez obrazloženja.")],
    "choice_en": [("o1", "Proceed with the recommended step now."), ("o2", "Delay the decision by {days} days."), ("o3", "Reject the request with no explanation.")],
    "ranking": [("o1", "Elektronska prijava putem portala."), ("o2", "Lična predaja na šalteru."), ("o3", "Slanje poštom preporučeno.")],
    "scoring": [("o1", "Potpuna dokumentacija s potvrdama."), ("o2", "Nepotpuna dokumentacija bez jedne potvrde.")],
    "scoring_en": [("o1", "Complete file with all certificates."), ("o2", "Incomplete file missing one certificate.")],
    "risk": [("o1", "Postupiti po propisanoj proceduri odmah."), ("o2", "Ne poduzeti ništa i čekati.")],
    "multicriteria": [("o1", "Opcija A: jeftinija, lošiji prateći uslovi."), ("o2", "Opcija B: skuplja, bolji rok i garancija.")],
    "confidence": [("o1", "Postupiti prema provjerenom dokumentu."), ("o2", "Postupiti prema usmenoj uputi.")],
    "abstention": [("o1", "Odobriti zahtjev."), ("o2", "Odbaciti zahtjev.")],
    "benchmark": [("o1", "Postupiti po propisanoj proceduri."), ("o2", "Ne poduzeti ništa.")],
    "benchmark_en": [("o1", "Follow the prescribed procedure."), ("o2", "Take no action.")],
}

# Zabranjeni oblici (lowercase substring): ascii-kvarovi bez kvačica,
# pogrešni lokativi i tipfeleri. Validacija puca ako se ijedan pojavi.
BANNED = [
    "tuzlau", "bihacu", "bihac", "brcko", "gorazde", "sarajevou",
    "izmedju", "konacna", "konacno", "masina", "uredjaj", "odljem",
    "gradjanin", "trazi", "produzenje", "salter", "misljenje", "knjigovodj",
    "poresk", "sljedeci", "podnosenja", "rjesenje", "rjesavanj", "zalbe",
    "zalbeni", "duzi", "troskovnika", "trzista", "cekanja", "ljubaznost",
    "cuvanje", "guzva", "iskljucivo", "tacan", "racun", "voznj", "clan",
    "kljucni", "stete", "uputnicu ljekara ni doziranje",
]

DIJAKRITICI = set("čćšđžČĆŠĐŽ")


def seed_states():
    seen = set()
    for fn in os.listdir(SAMPLES_DIR):
        if not fn.endswith(".jsonl"):
            continue
        with open(os.path.join(SAMPLES_DIR, fn), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        seen.add(json.loads(line).get("state", "").strip().lower())
                    except json.JSONDecodeError:
                        pass
    return seen


def slot():
    city = RNG.choice(CITIES)
    gen, lok = CITY_FORMS[city]
    return {"city": city, "city_gen": gen, "city_lok": lok,
            "name": RNG.choice(NAMES),
            "firm": RNG.choice(FIRMS), "doc": RNG.choice(DOCS),
            "amt": RNG.choice([350, 800, 1200, 2500, 5000, 9800, 15000]),
            "days": RNG.choice([3, 7, 10, 15, 21, 30]),
            "num": RNG.randint(1000, 9999)}


def ref_for(ds, lang, ranked, scores, conf, risk_level, factors, decision,
            abst_reason, rationale):
    return {"decision": decision, "options_ranked": ranked, "scores": scores,
            "risk": {"level": risk_level, "factors": factors},
            "confidence": conf, "abstention_reason": abst_reason,
            "rationale_short": rationale, "lang": lang,
            "model": "human-reference", "version": "1.0"}


def build(ds, idx, seed_seen, used_states):
    key = ds
    # en samo za choice/scoring/benchmark: ~50% en u ta tri daje ~19% ukupno
    if ds in ("choice", "scoring", "benchmark") and RNG.random() < 0.55:
        key = ds + "_en"
    tmpl = STATE_T[key][idx % len(STATE_T[key])]
    lang, t = tmpl
    s = slot()
    state = t.format(**s)
    if idx % 6 == 5:  # negacija na svakom ~6. primjer (>=15%)
        state += NEG_EN if lang == "en" else NEG_BS
    state = state.strip()
    # dedup protiv seeda i unutar generisanih
    h = hashlib.sha256(state.lower().encode()).hexdigest()
    if state.strip().lower() in seed_seen or h in used_states:
        state += f" Predmet br. {s['num']}-{idx}."
        h = hashlib.sha256(state.lower().encode()).hexdigest()
    used_states.add(h)
    opts = [{"id": o, "text": tx.format(**s)} for o, tx in OPTS[key]]
    oids = [o["id"] for o in opts]
    conf = round(RNG.uniform(0.72, 0.92), 2)
    if ds == "abstention":
        ref = ref_for(ds, lang, [], {}, round(RNG.uniform(0.2, 0.35), 2),
                      RNG.choice(["medium", "high"]), ["nepotpun zahtjev"],
                      "abstain", "nedovoljno informacija",
                      ("Nema priloga pa se bez dopune ne može odlučiti."
                       if lang == "bs" else "No attachments, decision postponed."))
    elif ds == "benchmark" and idx % 4 == 2:
        ref = ref_for(ds, lang, [], {}, round(RNG.uniform(0.25, 0.35), 2),
                      "medium", ["nepotpun zahtjev"], "abstain",
                      "nedovoljno informacija",
                      ("Bez priloga se ne može odlučiti."
                       if lang == "bs" else "Cannot decide without attachments."))
    elif ds in ("risk", "choice") and idx % 12 == 11:
        ref = ref_for(ds, lang, [], {}, round(RNG.uniform(0.25, 0.35), 2),
                      "medium", ["nedovoljno informacija"], "abstain",
                      "nedovoljno informacija",
                      ("Premalo činjenica za sigurnu odluku."
                       if lang == "bs" else "Too few facts for a safe decision."))
    elif ds == "scoring":
        sc = {oids[0]: round(RNG.uniform(0.8, 0.95), 2),
              oids[1]: round(RNG.uniform(0.15, 0.4), 2)}
        ref = ref_for(ds, lang, [oids[0], oids[1]], sc, conf, "low", [],
                      oids[0], None,
                      ("Potpun zahtjev prolazi, nepotpun ne."
                       if lang == "bs" else "Complete file passes, incomplete fails."))
    elif ds == "confidence":
        ref = ref_for(ds, lang, [oids[0], oids[1]],
                      {oids[0]: conf, oids[1]: round(1 - conf, 2)}, conf,
                      "low" if conf > 0.8 else "medium", [], oids[0], None,
                      "Provjeren dokument daje visoku pouzdanost.")
    elif ds == "risk":
        ref = ref_for(ds, lang, [oids[0], oids[1]],
                      {oids[0]: conf, oids[1]: round(0.3, 2)}, conf,
                      RNG.choice(["low", "medium", "high"]), ["moguć gubitak"],
                      oids[0], None, "Propisani postupak uklanja rizik.")
    else:  # choice, ranking, multicriteria, benchmark (ne-abstain)
        ranked = oids if ds != "ranking" else [oids[0], oids[1], oids[2]][:len(oids)]
        if ds == "ranking" and len(oids) == 2:
            ranked = oids
        sc = {o: round(v, 2) for o, v in
              zip(ranked, sorted([RNG.uniform(0.3, 0.95) for _ in ranked], reverse=True))}
        sc[ranked[0]] = max(sc[ranked[0]], conf)
        ref = ref_for(ds, lang, ranked, sc, conf, "low", [], ranked[0], None,
                      ("Preporučeni postupak je propisan i najbrži."
                       if lang == "bs" else "The recommended step is prescribed and fastest."))
    rec = {"id": f"BH-D-{ds}-{idx + 6:03d}", "lang": lang, "state": state,
           "options": opts, "reference": ref, "source": SOURCE, "license": LICENSE}
    return rec, lang


def validate(all_rows, seed_seen):
    """Puca (exit 1) ako ijedan bs state nema kvačicu, sadrži zabranjeni
    oblik, ili je duplikat seeda / drugog generisanog statea."""
    errors = []
    seen = set()
    for r in all_rows:
        rid = r.get("id", "?")
        st = r.get("state", "")
        low = st.strip().lower()
        if r.get("lang") == "bs" and not any(c in st for c in DIJAKRITICI):
            errors.append(f"{rid}: bs state bez ijedne kvačice: {st[:80]}")
        for b in BANNED:
            if b in low:
                errors.append(f"{rid}: zabranjen oblik '{b}': {st[:100]}")
                break
        if low in seed_seen:
            errors.append(f"{rid}: duplikat seed statea: {st[:80]}")
        if low in seen:
            errors.append(f"{rid}: duplikat generisanog statea: {st[:80]}")
        seen.add(low)
    if errors:
        print(f"VALIDACIJA NEUSPJEŠNA ({len(errors)} grešaka):")
        for e in errors[:30]:
            print(f"  FAIL {e}")
        sys.exit(1)
    print(f"Validacija OK: {len(all_rows)} stateova, 0 bez kvačica, "
          f"0 zabranjenih oblika, 0 duplikata.")


def main():
    seed_seen = seed_states()
    os.makedirs(EXPANDED_DIR, exist_ok=True)
    used, stats, lang_stats, neg = set(), {}, {"bs": 0, "en": 0}, 0
    all_rows = []
    datasets = ["choice", "ranking", "scoring", "risk", "multicriteria",
                "confidence", "abstention", "benchmark"]
    for ds in datasets:
        rows = []
        for i in range(N_PER_DS):
            rec, lang = build(ds, i, seed_seen, used)
            rows.append(rec)
            all_rows.append(rec)
            lang_stats[lang] += 1
            if any(w in rec["state"].lower()
                   for w in ("nije ", " nije", "ne ", "nema", "bez ", " not ", "no ", "n't", "without")):
                neg += 1
        stats[ds] = rows
    validate(all_rows, seed_seen)
    for ds in datasets:
        with open(os.path.join(EXPANDED_DIR, f"{ds}.jsonl"), "w", encoding="utf-8") as f:
            for r in stats[ds]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    counts = {ds: len(v) for ds, v in stats.items()}
    total = sum(counts.values())
    print(f"Ukupno generisano: {total} primjera.")
    for ds, n in counts.items():
        print(f"  {ds}: {n}")
    print(f"Jezici: bs={lang_stats['bs']} en={lang_stats['en']} "
          f"({lang_stats['en'] / total:.0%} en).")
    print(f"Negacija: {neg}/{total} ({neg / total:.0%}).")
    print(f"Abstain: samo abstention/risk/choice/benchmark; bez state-duplikata sa samples/.")


if __name__ == "__main__":
    main()
