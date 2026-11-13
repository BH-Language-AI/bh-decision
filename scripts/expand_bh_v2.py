#!/usr/bin/env python3
"""Ekspanzija v0.3: 8 kategorija x ~250 = ~2000 stavki, ijekavica primarno (80/20 en).
Deterministički (seed 13), dedup protiv heldout-v1 i unutar batcha, manifest s hash.
Shema identična v0.2 (template-expansion), licenca CC-BY-4.0.
"""
import hashlib
import json
import os
import random

R = random.Random(13)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "expanded-v2")
os.makedirs(OUT, exist_ok=True)

IMENA = ["Goran Lukić", "Amina Hodžić", "Marko Jurić", "Lejla Softić", "Ivan Kovačević",
         "Selma Delić", "Petar Pavlović", "Emina Jahić", "Jovan Simić", "Alma Kurtić",
         "Nihad Fejzić", "Maja Tomić", "Adnan Smajić", "Ivana Babić", "Kenan Mujkić",
         "Dževad Karić", "Snježana Lovrić", "Mirza Džafić", "Tanja Vuković", "Sead Hasić",
         "Branko Marić", "Fatima Alić", "Goran Tadić", "Aida Bešlić", "Milan Stojanović",
         "Hana Dedić", "Slaven Knez", "Merima Omerović", "Dražen Perić", "Azra Čaušević",
         "Vedad Hadžić", "Nataša Blagojević", "Emir Subašić", "Jelena Rajić", "Tarik Mehić",
         "Sandra Zorić", "Damir Krdžalić", "Lejla Begović", "Igor Stanković", "Amela Gegić"]
GRADOVI = ["Sarajeva", "Tuzle", "Mostara", "Zenice", "Bihaća", "Banje Luke", "Brčkog", "Trebinja",
           "Foče", "Goražda", "Konjica", "Livna", "Orašja", "Sanskog Mosta",
           "Visokog", "Zavidovića"]
USTANOVE = ["Porezna uprava", "MUP", "Općina Centar", "Zavod za zapošljavanje", "Katastar", "Dom zdravlja",
            "Općina Novi Grad", "Centar za socijalni rad", "Zavod MIO", "Gruntovnica"]
DOK = ["pasoš", "ličnu kartu", "vozačku dozvolu", "građevinsku dozvolu", "radnu knjižicu",
       "uvjerenje o državljanstvu", "izvod iz matične knjige", "dozvolu za rad"]
DANA = ["7 dana", "15 dana", "21 dan", "30 dana", "8 dana", "10 dana"]

EN_NAMES = ["John Miller", "Sara Ahmed", "Mark Stone", "Leila Hasic", "Ivan Kovacs"]
EN_CITIES = ["Sarajevo", "Tuzla", "Mostar", "Zenica", "Bihac"]
EN_OFF = ["Tax office", "City hall", "Registry office", "Health center"]


def ref(decision, ranked, scores, risk="low", factors=(), conf=0.85, rat="", lang="bs"):
    return {"decision": decision, "options_ranked": ranked, "scores": scores,
            "risk": {"level": risk, "factors": list(factors)}, "confidence": conf,
            "abstention_reason": None, "rationale_short": rat, "lang": lang,
            "model": "human-reference", "version": "1.0"}


def item(cat, i, lang, state, options, reference):
    return {"id": f"BH-D2-{cat}-{i:04d}", "lang": lang, "state": state,
            "options": [{"id": k, "text": t} for k, t in options],
            "reference": reference, "source": "template-expansion-v0.3", "license": "CC-BY-4.0"}


G = {}


def g_choice(n):
    out = []
    for i in range(n):
        en = R.random() < 0.2
        if en:
            nm, gr, us, dk, dn = R.choice(EN_NAMES), R.choice(EN_CITIES), R.choice(EN_OFF), "passport", R.choice(["7 days", "15 days", "21 days"])
            st = f"{nm} from {gr} requests document renewal ({dk}). The {us} offers three procedures."
            o = [("o1", "Accept the recommended procedure on time."), ("o2", f"Delay the decision by {dn}."),
                 ("o3", "Reject the request without explanation.")]
            r = ref("o1", ["o1", "o2", "o3"], {"o1": 0.88, "o2": 0.4, "o3": 0.1}, conf=0.86,
                    rat="The recommended procedure is prescribed and fastest.", lang="en")
        else:
            t = R.randrange(5)
            nm, gr, us, dk, dn = R.choice(IMENA), R.choice(GRADOVI), R.choice(USTANOVE), R.choice(DOK), R.choice(DANA)
            if t == 0:
                st = f"Građanin {nm} iz {gr} traži produženje dokumenta ({dk}). Na šalteru ustanove {us} nude se tri postupka."
            elif t == 1:
                st = f"Na šalteru ustanove {us} stranka {nm} iz {gr} podnosi zahtjev za ({dk}). Rok za dopunu je {dn}."
            elif t == 2:
                st = f"{nm} iz {gr} čeka rješenje o dokumentu ({dk}); {us} traži dopunu u roku od {dn}."
            elif t == 3:
                st = f"Zahtjev stranke {nm} ({gr}, {dk}) zaprimljen je u ustanovi {us}. Moguća su tri ishoda."
            else:
                st = f"Ustanova {us}: predmet {nm} iz {gr} — produženje dokumenta ({dk}), rok {dn}."
            o = [("o1", "Prihvatiti preporučeni postupak u roku."), ("o2", f"Odgoditi odluku za {dn}."),
                 ("o3", "Odbaciti zahtjev bez obrazloženja.")]
            r = ref("o1", ["o1", "o2", "o3"], {"o1": 0.88, "o2": 0.4, "o3": 0.1}, conf=0.86,
                    rat="Preporučeni postupak je propisan i najbrži.")
        out.append(item("choice", i, "en" if en else "bs", st, o, r))
    return out


def g_risk(n):
    out = []
    for i in range(n):
        en = R.random() < 0.2
        if en:
            st = f"A contractor offers {R.choice(EN_NAMES)} a {R.choice(['roof repair', 'heating fix', 'facade job'])} without warranty, {R.choice(['two days', 'a week'])} before the rainy season."
            o = [("o1", "Sign with warranty clause."), ("o2", "Sign without warranty."), ("o3", "Postpone past the season.")]
            r = ref("o1", ["o1", "o3", "o2"], {"o1": 0.8, "o2": 0.1, "o3": 0.3}, risk="high",
                    factors=["water damage"], conf=0.8, rat="No-warranty work before rain is an unacceptable risk.", lang="en")
        else:
            t = R.randrange(5)
            nm, gr = R.choice(IMENA), R.choice(GRADOVI)
            posao = R.choice(["popravak krova", "zamjenu grijanja", "fasadu", "stolariju"])
            rok = R.choice(["kišne sezone", "zime", "inspekcije", "rokova"])
            if t == 0:
                st = f"Izvođač nudi građaninu {nm} iz {gr} {posao} bez garancije, neposredno pred {rok}."
            elif t == 1:
                st = f"{nm} iz {gr} mora odlučiti o ponudi za {posao}: bez garancije, a {rok} se bliži."
            elif t == 2:
                st = f"Pred {rok}, {nm} ({gr}) dobija ponudu za {posao} — jeftinije, ali bez garancije."
            elif t == 3:
                st = f"Za {posao} u {gr}, {nm} bira između skuplje ponude s garancijom i jeftinije bez nje, pred {rok}."
            else:
                st = f"{us_ustanova()} upozorava: {nm} iz {gr} planira {posao} bez garancije pred {rok}."
            o = [("o1", "Potpisati uz klauzulu o garanciji."), ("o2", "Potpisati bez garancije."), ("o3", "Odgoditi poslije sezone.")]
            r = ref("o1", ["o1", "o3", "o2"], {"o1": 0.8, "o2": 0.1, "o3": 0.3}, risk="high",
                    factors=["materijalna šteta"], conf=0.8, rat="Rad bez garancije pred sezonu je neprihvatljiv rizik.")
        out.append(item("risk", i, "en" if en else "bs", st, o, r))
    return out


def us_ustanova():
    return R.choice(["Inspekcija", "Savjet mjesne zajednice", "Udruženje potrošača"])


def g_ranking(n):
    out = []
    kanali = [("e-uprava", "Elektronska prijava putem portala e-Uprava."),
              ("salter", "Lični dolazak na šalter sa potvrdama."),
              ("posta", "Slanje poštom s povratnicom.")]
    for i in range(n):
        en = R.random() < 0.2
        R.shuffle(kanali)
        ids = [k for k, _ in kanali]
        if en:
            st = f"{R.choice(EN_NAMES)} must submit a {R.choice(['permit request', 'appeal', 'registration'])} to the {R.choice(EN_OFF)}."
            o = [(k, {"e-uprava": "Online portal submission.", "salter": "In-person visit.",
                      "posta": "Registered mail."}[k]) for k in ids]
            r = ref(ids[0], ids, {k: round(v, 2) for k, v in zip(ids, [0.85, 0.4, 0.3])},
                    conf=0.82, rat="Ranked by speed and traceability.", lang="en")
        else:
            t = R.randrange(4)
            nm, dk = R.choice(IMENA), R.choice(DOK)
            if t == 0:
                st = f"{nm} predaje zahtjev za ({dk}) i bira kanal podnošenja."
            elif t == 1:
                st = f"Za ({dk}), {nm} rangira načine predaje po brzini i dokazivosti."
            elif t == 2:
                st = f"Stranka {nm}: podnošenje zahtjeva za ({dk}) — portal, šalter ili pošta?"
            else:
                st = f"Koji kanal je najbolji za zahtjev stranke {nm} ({dk})?"
            o = [(k, t_) for k, t_ in kanali]
            r = ref(ids[0], ids, {k: round(v, 2) for k, v in zip(ids, [0.85, 0.4, 0.3])},
                    conf=0.82, rat="Rangirano po brzini i dokazivosti.")
        out.append(item("ranking", i, "en" if en else "bs", st, o, r))
    return out


def g_scoring(n):
    out = []
    docs = ["spisa", "predmeta", "dosjea", "zahtjeva", "prijave"]
    for i in range(n):
        en = R.random() < 0.2
        if en:
            st = f"Score the completeness of {R.choice(EN_NAMES)}'s application file."
            o = [("o1", "Full file with certificates."), ("o2", "Partial file, one paper missing.")]
            r = ref("o1", ["o1", "o2"], {"o1": 0.9, "o2": 0.45}, conf=0.88,
                    rat="Completeness is binary-checkable.", lang="en")
        else:
            nm, dc = R.choice(IMENA), R.choice(docs)
            t = R.randrange(6)
            if t == 0:
                st = f"Ocijeniti potpunost {dc} stranke {nm}."
            elif t == 1:
                st = f"{dc.capitalize()} stranke {nm}: bodovati urednost dokumentacije."
            elif t == 2:
                st = f"Koliko je uredan {dc} stranke {nm}?"
            elif t == 3:
                st = f"Provjera {dc} ({nm}): ocijeniti kompletnost priloga."
            elif t == 4:
                st = f"Ustanova {R.choice(USTANOVE)} provjerava {dc} stranke {nm}."
            else:
                st = f"Bodovanje {dc}: stranka {nm}, {R.choice(GRADOVI)}."
            o = [("o1", "Potpuna dokumentacija s potvrdama."), ("o2", "Djelimična, fali jedan prilog.")]
            r = ref("o1", ["o1", "o2"], {"o1": 0.9, "o2": 0.45}, conf=0.88,
                    rat="Potpunost se provjerava binarno.")
        out.append(item("scoring", i, "en" if en else "bs", st, o, r))
    return out


def g_multi(n):
    out = []
    usluge = ["šalter A i šalter B", "red na šalteru i e-Upravu", "dva šaltera gradske uprave"]
    for i in range(n):
        en = R.random() < 0.2
        if en:
            st = f"{R.choice(['Counter A is near but queues are long; counter B is farther but fast.', 'The downtown office has a long line; the suburban office is empty.', 'Online filing is down for maintenance; two walk-in offices are open.'])} {R.choice(EN_NAMES)} chooses in {R.choice(EN_CITIES)}."
            o = [("o1", "Counter A: near, long queues."), ("o2", "Counter B: farther, no wait."),
                 ("o3", "Come back another day.")]
            r = ref("o2", ["o2", "o1", "o3"], {"o1": 0.5, "o2": 0.8, "o3": 0.2}, conf=0.78,
                    rat="Time cost dominates distance.", lang="en")
        else:
            t = R.randrange(6)
            nm, gr = R.choice(IMENA), R.choice(GRADOVI)
            if t == 0:
                st = f"Šalter A: blizu, ali redovi su dugi. Šalter B: dalje, bez čekanja. {nm} bira."
            elif t == 1:
                st = f"{nm} vaga: blizina šaltera A protiv čekanja, ili dalji šalter B bez reda."
            elif t == 2:
                st = f"Dvije opcije za {nm}: čekati u redu blizu ili ići dalje bez čekanja."
            elif t == 3:
                st = f"{nm} mora odvagnuti udaljenost i vrijeme čekanja na šalterima."
            elif t == 4:
                st = f"U {gr}, {nm} bira između reda na šalteru i e-Uprave od kuće."
            else:
                st = f"{nm} ({gr}): {R.choice(usluge)} — šta je brže?"
            o = [("o1", "Šalter A: blizu, ali redovi su dugi."), ("o2", "Šalter B: dalje, bez čekanja."),
                 ("o3", "Vratiti se drugi dan.")]
            r = ref("o2", ["o2", "o1", "o3"], {"o1": 0.5, "o2": 0.8, "o3": 0.2}, conf=0.78,
                    rat="Trošak vremena nadmašuje udaljenost.")
        out.append(item("multicriteria", i, "en" if en else "bs", st, o, r))
    return out


def g_conf(n):
    out = []
    for i in range(n):
        en = R.random() < 0.2
        if en:
            st = f"{R.choice(EN_NAMES)} filed the {R.choice(['form', 'appeal'])} on the prescribed template."
            o = [("o1", "Filed on the prescribed form."), ("o2", "Filed on plain paper.")]
            r = ref("o1", ["o1", "o2"], {"o1": 0.95, "o2": 0.3}, conf=0.95,
                    rat="Template compliance is verifiable.", lang="en")
        else:
            nm, dc = R.choice(IMENA), R.choice(DOK)
            t = R.randrange(6)
            if t == 0:
                st = f"{nm} je predao zahtjev za ({dc}) na propisanom obrascu."
            elif t == 1:
                st = f"Zahtjev stranke {nm} za ({dc}) podnesen je na važećem formularu."
            elif t == 2:
                st = f"Obrazac stranke {nm} je propisan i potpisan."
            elif t == 3:
                st = f"Ustanova {R.choice(USTANOVE)} zaprimila je uredan obrazac ({nm}, {dc})."
            elif t == 4:
                st = f"Stranka {nm} ({R.choice(GRADOVI)}) ima potpun obrazac za ({dc})."
            else:
                st = f"Predmet ({dc}): {nm} dostavio propisanu dokumentaciju."
            o = [("o1", "Predato na propisanom obrascu."), ("o2", "Predato na običnom papiru.")]
            r = ref("o1", ["o1", "o2"], {"o1": 0.95, "o2": 0.3}, conf=0.95,
                    rat="Usklađenost s obrascem je provjerljiva.")
        out.append(item("confidence", i, "en" if en else "bs", st, o, r))
    return out


def g_abstain(n):
    out = []
    for i in range(n):
        en = R.random() < 0.2
        if en:
            st = f"Request #{R.randrange(1000, 9999)} with no readable content attached."
            o = [("o1", "Approve the request."), ("o2", "Ask for a supplement.")]
            r = {"decision": "abstain", "options_ranked": [], "scores": {}, "risk": {"level": "medium", "factors": ["no data"]},
                 "confidence": 0.25, "abstention_reason": "insufficient information",
                 "rationale_short": "No readable content to decide on.", "lang": "en", "model": "human-reference", "version": "1.0"}
        else:
            t = R.randrange(3)
            br = R.randrange(1000, 9999)
            if t == 0:
                st = f"Zahtjev broj {br} bez čitljivog sadržaja u prilogu."
            elif t == 1:
                st = f"Predmet {br}: prilog nečitljiv, sadržaj nepoznat."
            else:
                st = f"Nečitljiv podnesak (predmet {br}); nema osnova za odluku."
            o = [("o1", "Odobriti zahtjev."), ("o2", "Tražiti dopunu.")]
            r = {"decision": "abstain", "options_ranked": [], "scores": {}, "risk": {"level": "medium", "factors": ["nema podataka"]},
                 "confidence": 0.25, "abstention_reason": "nedovoljno informacija",
                 "rationale_short": "Nema čitljivog sadržaja za odluku.", "lang": "bs", "model": "human-reference", "version": "1.0"}
        out.append(item("abstention", i, "en" if en else "bs", st, o, r))
    return out


def g_bench(n):
    out = []
    for i in range(n):
        en = R.random() < 0.2
        if en:
            st = f"Extend the {R.choice(['ID card', 'passport', 'driving licence'])} at the municipality of residence in {R.choice(EN_CITIES)}."
            o = [("o1", "Apply at the counter of the home municipality."), ("o2", "Apply in another city without grounds.")]
            r = ref("o1", ["o1", "o2"], {"o1": 0.9, "o2": 0.3}, conf=0.9,
                    rat="Jurisdiction rule is explicit.", lang="en")
        else:
            dk, gr = R.choice(DOK), R.choice(GRADOVI)
            t = R.randrange(6)
            if t == 0:
                st = f"Produžiti ({dk}) u općini stanovanja ({gr})."
            elif t == 1:
                st = f"({dk}) se produžava u općini prebivališta ({gr})."
            elif t == 2:
                st = f"Za produženje ({dk}) nadležna je općina stanovanja."
            elif t == 3:
                st = f"Stranka iz {gr} traži produženje dokumenta ({dk}) na matičnom šalteru."
            elif t == 4:
                st = f"Gdje se produžava ({dk}) za stanovnika ({gr})?"
            else:
                st = f"Općina {gr}: produženje dokumenta ({dk}), matični šalter."
            o = [("o1", "Predati na šalteru matične općine."), ("o2", "Predati u drugom gradu bez osnova.")]
            r = ref("o1", ["o1", "o2"], {"o1": 0.9, "o2": 0.3}, conf=0.9,
                    rat="Pravilo nadležnosti je izričito.")
        out.append(item("benchmark", i, "en" if en else "bs", st, o, r))
    return out


G = {"choice": g_choice, "risk": g_risk, "ranking": g_ranking, "scoring": g_scoring,
     "multicriteria": g_multi, "confidence": g_conf, "abstention": g_abstain, "benchmark": g_bench}
PER_CAT = {"choice": 300, "risk": 300, "ranking": 450, "scoring": 350, "multicriteria": 600,
           "confidence": 350, "abstention": 300, "benchmark": 600}

held = set()
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "heldout", "heldout-v1.jsonl")):
    if l.strip():
        held.add(json.loads(l)["state"].strip().lower())

manifest = {"seed": 13, "source": "template-expansion-v0.3", "license": "CC-BY-4.0", "files": {}}
for cat, fn in G.items():
    recs, seen = [], set()
    for r in fn(PER_CAT[cat]):
        key = r["state"].strip().lower()
        if key in seen or key in held:
            continue
        seen.add(key)
        recs.append(r)
    # renumeriši nakon dedupa
    for j, r in enumerate(recs):
        r["id"] = f"BH-D2-{cat}-{j:04d}"
    path = os.path.join(OUT, f"{cat}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    manifest["files"][cat] = {"n": len(recs), "sha256": h}
    print(cat, len(recs))
manifest["total"] = sum(v["n"] for v in manifest["files"].values())
json.dump(manifest, open(os.path.join(OUT, "manifest-v0.3.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", manifest["total"])
