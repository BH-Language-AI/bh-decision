#!/usr/bin/env python3
"""Ekspanzija v0.4 — balansiranje: o2/o3/abstain unutar svih kategorija + dvosmisleni.
Deterministički (seed 44), dedup protiv heldout-v1 i v0.3, manifest, CC-BY-4.0.
"""
import hashlib
import json
import os
import random

R = random.Random(44)
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "datasets", "expanded-v04")
os.makedirs(OUT, exist_ok=True)

IMENA = ["Goran Lukić", "Amina Hodžić", "Marko Jurić", "Lejla Softić", "Ivan Kovačević",
         "Selma Delić", "Petar Pavlović", "Emina Jahić", "Jovan Simić", "Alma Kurtić",
         "Nihad Fejzić", "Maja Tomić", "Adnan Smajić", "Ivana Babić", "Kenan Mujkić",
         "Dževad Karić", "Snježana Lovrić", "Mirza Džafić", "Tanja Vuković", "Sead Hasić"]
GRADOVI = ["Sarajeva", "Tuzle", "Mostara", "Zenice", "Bihaća", "Banje Luke", "Brčkog", "Trebinja"]
DOK = ["pasoš", "ličnu kartu", "vozačku dozvolu", "građevinsku dozvolu", "radnu knjižicu",
       "uvjerenje o državljanstvu", "izvod iz matične knjige", "dozvolu za rad"]
USTANOVE = ["Porezna uprava", "MUP", "Općina Centar", "Zavod za zapošljavanje", "Katastar", "Dom zdravlja",
            "Općina Novi Grad", "Centar za socijalni rad"]


def item(cat, i, lang, state, options, reference):
    return {"id": f"BH-D4-{cat}-{i:04d}", "lang": lang, "state": state,
            "options": [{"id": k, "text": t} for k, t in options],
            "reference": reference, "source": "template-expansion-v0.4", "license": "CC-BY-4.0"}


def ref(decision, ranked, scores, risk="low", factors=(), conf=0.8, rat="", abst=None, lang="bs"):
    return {"decision": decision, "options_ranked": ranked, "scores": scores,
            "risk": {"level": risk, "factors": list(factors)}, "confidence": conf,
            "abstention_reason": abst, "rationale_short": rat, "lang": lang,
            "model": "human-reference", "version": "1.0"}


G = {}

# --- choice: o2 (odgoda ispravna) i o3 (odbijanje ispravno) ---
def g_choice(n):
    out = []
    for i in range(n):
        v = R.random()
        nm, gr = R.choice(IMENA), R.choice(GRADOVI)
        if v < 0.5:  # o2: dokumentacija nepotpuna, rok daleko
            t = R.randrange(3)
            if t == 0:
                st = f"Zahtjev stranke {nm} ({gr}) je nepotpun, a rok za dopunu traje još mjesec dana."
            elif t == 1:
                st = f"{nm} iz {gr} predao je zahtjev bez ključnog priloga; rok ne ističe skoro."
            else:
                st = f"Predmet {nm} ({gr}): fali dokaz o uplati, vremena za dopunu ima."
            o = [("o1", "Prihvatiti nepotpun zahtjev odmah."), ("o2", "Odgoditi i tražiti dopunu."),
                 ("o3", "Odbaciti zahtjev bez obrazloženja.")]
            r = ref("o2", ["o2", "o1", "o3"], {"o1": 0.3, "o2": 0.8, "o3": 0.1}, conf=0.8,
                    rat="Nepotpun zahtjev se dopunjava, ne odbacuje niti prihvata.")
        else:  # o3: falsifikat / nenadležnost
            t = R.randrange(3)
            if t == 0:
                st = f"U zahtjevu stranke {nm} ({gr}) otkriven je falsifikovan prilog."
            elif t == 1:
                st = f"{nm} iz {gr} traži dokument za koji ova ustanova uopšte nije nadležna, uz prijetnje."
            else:
                st = f"Predmet {nm} ({gr}): podnesak je krivotvoren, potpis ne odgovara."
            o = [("o1", "Prihvatiti sumnjiv zahtjev."), ("o2", "Odgoditi unedogled."),
                 ("o3", "Odbaciti uz obrazloženje i prijavu.")]
            r = ref("o3", ["o3", "o2", "o1"], {"o1": 0.05, "o2": 0.3, "o3": 0.85},
                    risk="high", factors=["falsifikat"], conf=0.85,
                    rat="Falsifikat se odbacuje uz prijavu, ne odgađa.")
        out.append(item("choice", i, "bs", st, o, r))
    return out

# --- risk: o2 (preuzeti rizik ispravno — nizak ulog) i o3 (odustati) ---
def g_risk(n):
    out = []
    for i in range(n):
        v = R.random()
        nm, gr = R.choice(IMENA), R.choice(GRADOVI)
        if v < 0.5:  # o2: sitan iznos, garancija nebitna
            st = f"{nm} iz {gr} kupuje {R.choice(['produžni kabl', 'metlu', 'sijalicu', 'olovke'])} bez garancije za sitan iznos."
            o = [("o1", "Tražiti pismenu garanciju."), ("o2", "Kupiti bez garancije."),
                 ("o3", "Odustati od kupovine.")]
            r = ref("o2", ["o2", "o1", "o3"], {"o1": 0.3, "o2": 0.85, "o3": 0.1}, conf=0.85,
                    rat="Za sitan iznos trošak garancijske procedure nadmašuje rizik.")
        else:  # o3: previsok rizik, odustati
            st = f"{nm} iz {gr} nudi {R.choice(['ulaganje u neprovjereni fond', 'kupovinu auta bez papira', 'kredit uz zalog stana'])}."
            o = [("o1", "Prihvatiti odmah."), ("o2", "Prihvatiti djelimično."),
                 ("o3", "Odustati od posla.")]
            r = ref("o3", ["o3", "o2", "o1"], {"o1": 0.05, "o2": 0.25, "o3": 0.9},
                    risk="high", factors=["gubitak imovine"], conf=0.9,
                    rat="Nepovratan gubitak se izbjegava odustajanjem, ne djelimičnim rizikom.")
        out.append(item("risk", i, "bs", st, o, r))
    return out

# --- scoring: o2 (nepotpuno) + o3? scoring ima 2 opcije; o2-correct + apstinencija ---
def g_scoring(n):
    out = []
    for i in range(n):
        v = R.random()
        nm, dc = R.choice(IMENA), R.choice(DOK)
        if v < 0.6:  # o2 ispravno: nepotpuno
            t = R.randrange(4)
            if t == 0:
                st = f"Spis stranke {nm} ({dc}): fale {R.choice(['dva priloga', 'potpis', 'pečat', 'dokaz o uplati'])}."
            elif t == 1:
                st = f"Ustanova {R.choice(USTANOVE)} vraća {dc} stranke {nm} na dopunu."
            elif t == 2:
                st = f"{dc.capitalize()} stranke {nm} je nepotpun; fali ključni prilog."
            else:
                st = f"Provjera: {dc} ({nm}) — dokumentacija djelimična."
            o = [("o1", "Potpuna dokumentacija."), ("o2", "Nepotpuna dokumentacija.")]
            r = ref("o2", ["o2", "o1"], {"o1": 0.2, "o2": 0.85}, conf=0.85,
                    rat="Nedostaci su konkretni i provjerljivi.")
        else:  # apstinencija: spis nedostupan
            st = f"Spis stranke {nm} ({R.choice(DOK)}) trenutno nije dostupan (u arhivi drugog grada)."
            o = [("o1", "Potpuna dokumentacija."), ("o2", "Nepotpuna dokumentacija.")]
            r = ref("abstain", [], {}, conf=0.3, abst="spis nedostupan",
                    rat="Bez uvida u spis nema ocjene.")
        out.append(item("scoring", i, "bs", st, o, r))
    return out

# --- benchmark: o2 (pogrešna općina) + apstinencija ---
def g_benchmark(n):
    out = []
    for i in range(n):
        v = R.random()
        nm, gr, dk = R.choice(IMENA), R.choice(GRADOVI), R.choice(DOK)
        if v < 0.6:
            st = f"{nm} stanovnik je {gr}, a zahtjev za ({dk}) je greškom predat u drugoj općini."
            o = [("o1", "Predati na matičnom šalteru."), ("o2", "Ostaviti u pogrešnoj općini.")]
            r = ref("o2", ["o2", "o1"], {"o1": 0.2, "o2": 0.85}, conf=0.85,
                    rat="Nadležnost je vezana za prebivalište; pogrešna općina odbacuje.")
        else:
            st = f"Zahtjev za ({R.choice(DOK)}) bez oznake podnosioca i bez adrese prebivališta."
            o = [("o1", "Predati na matičnom šalteru."), ("o2", "Predati bilo gdje.")]
            r = ref("abstain", [], {}, conf=0.25, abst="nepoznat podnosilac",
                    rat="Bez identiteta nema nadležnosti.")
        out.append(item("benchmark", i, "bs", st, o, r))
    return out

# --- confidence: o2 (nepropisno) ---
def g_conf(n):
    out = []
    for i in range(n):
        nm, dk = R.choice(IMENA), R.choice(DOK)
        v = R.random()
        if v < 0.7:
            t = R.randrange(3)
            if t == 0:
                st = f"Zahtjev stranke {nm} za ({dk}) pisan je rukom na poleđini računa, pečata nema."
            elif t == 1:
                st = f"{nm} predao ({dk}) na običnom papiru bez zaglavlja ustanove {R.choice(USTANOVE)}."
            else:
                st = f"Podnesak za ({dk}), stranka {nm}: nema propisanog obrasca."
            o = [("o1", "Predato na propisanom obrascu."), ("o2", "Nije na propisanom obrascu.")]
            r = ref("o2", ["o2", "o1"], {"o1": 0.1, "o2": 0.9}, conf=0.9,
                    rat="Račun nije propisan obrazac.")
        else:
            st = f"Obrazac stranke {nm} za ({dk}) poderan je preko ključnog polja."
            o = [("o1", "Predato na propisanom obrascu."), ("o2", "Nije na propisanom obrascu.")]
            r = ref("abstain", [], {}, conf=0.3, abst="nečitljiv obrazac",
                    rat="Poderanina preko ključnog polja onemogućava ocjenu.")
        out.append(item("confidence", i, "bs", st, o, r))
    return out

# --- multicriteria: o1/o3 (čekanje pobjeđuje / drugi dan) ---
def g_multi(n):
    out = []
    for i in range(n):
        v = R.random()
        nm, gr = R.choice(IMENA), R.choice(GRADOVI)
        if v < 0.5:  # o1: hitno, blizina pobjeđuje
            st = f"{nm} iz {gr} mora hitno ovjeriti dokument; šalter A je blizu s redom, šalter B daleko bez reda, a rok ističe danas."
            o = [("o1", "Šalter A: blizu, redovi."), ("o2", "Šalter B: daleko, bez čekanja."),
                 ("o3", "Vratiti se drugi dan.")]
            r = ref("o1", ["o1", "o2", "o3"], {"o1": 0.8, "o2": 0.5, "o3": 0.05}, conf=0.8,
                    rat="Rok danas isključuje sutra; blizina nadmašuje red.")
        else:  # o3: oba zatvorena / gužva svugdje
            st = f"U {gr} su oba šaltera pred zatvaranjem s dugim redovima; {nm} ne žuri."
            o = [("o1", "Šalter A: stati u red."), ("o2", "Šalter B: stati u red."),
                 ("o3", "Vratiti se drugi dan.")]
            r = ref("o3", ["o3", "o1", "o2"], {"o1": 0.3, "o2": 0.3, "o3": 0.85}, conf=0.85,
                    rat="Bez žurbe je čekanje pred zatvaranjem čisti gubitak.")
        out.append(item("multicriteria", i, "bs", st, o, r))
    return out

# --- ranking: rotacija ispravnog kanala ---
def g_rank(n):
    out = []
    for i in range(n):
        v = R.random()
        nm, gr = R.choice(IMENA), R.choice(GRADOVI)
        if v < 0.4:  # pošta: treba dokaz o slanju, portal pao
            st = f"Portal e-Uprave je u kvaru, a {nm} iz {gr} mora dokazati datum slanja."
            o = [("e-uprava", "Portal (u kvaru)."), ("salter", "Šalter."), ("posta", "Pošta s povratnicom.")]
            r = ref("posta", ["posta", "salter", "e-uprava"], {"e-uprava": 0.05, "salter": 0.5, "posta": 0.9}, conf=0.9,
                    rat="Samo povratnica dokazuje datum kad portal ne radi.")
        elif v < 0.7:  # šalter: hitan potpis uživo
            st = f"{nm} iz {gr} mora lično potpisati pred službenikom još danas."
            o = [("e-uprava", "Portal."), ("salter", "Šalter uživo."), ("posta", "Pošta.")]
            r = ref("salter", ["salter", "posta", "e-uprava"], {"e-uprava": 0.2, "salter": 0.9, "posta": 0.4}, conf=0.9,
                    rat="Lični potpis traži fizičko prisustvo.")
        else:  # e-uprava: redovan slučaj
            st = f"Redovan zahtjev stranke {nm} iz {gr}, bez žurbe i bez potpisa uživo."
            o = [("e-uprava", "Portal od kuće."), ("salter", "Šalter."), ("posta", "Pošta.")]
            r = ref("e-uprava", ["e-uprava", "posta", "salter"], {"e-uprava": 0.9, "posta": 0.4, "salter": 0.3}, conf=0.9,
                    rat="Bez posebnih zahtjeva portal je najbrži.")
        out.append(item("ranking", i, "bs", st, o, r))
    return out

# --- abstention: apstinencija i u 3-opcijskim + dvosmisleni s niskim confidence ---
def g_abst(n):
    out = []
    for i in range(n):
        v = R.random()
        if v < 0.5:
            st = f"Zahtjev #{R.randrange(1000, 9999)}: prilog je prazan fajl od 0 bajtova."
            o = [("o1", "Odobriti."), ("o2", "Odbiti."), ("o3", "Tražiti dopunu.")]
            r = ref("abstain", [], {}, conf=0.2, abst="prazan prilog", rat="Prazan fajl nosi nula informacija.")
        else:
            st = f"Stranka tvrdi suprotno od onoga što piše u prilogu; oboje izgleda uvjerljivo (predmet #{R.randrange(1000, 9999)})."
            o = [("o1", "Vjerovati stranci."), ("o2", "Vjerovati prilogu."), ("o3", "Tražiti treći dokaz.")]
            r = ref("o3", ["o3", "o1", "o2"], {"o1": 0.35, "o2": 0.35, "o3": 0.55}, conf=0.55,
                    rat="Podjednako uvjerljive suprotnosti traže treći dokaz; povjerenje nisko.")
        out.append(item("abstention", i, "bs", st, o, r))
    return out


G = {"choice": (g_choice, 350), "risk": (g_risk, 300), "scoring": (g_scoring, 450), "benchmark": (g_benchmark, 450), "confidence": (g_conf, 450), "multicriteria": (g_multi, 350),
     "ranking": (g_rank, 350), "abstention": (g_abst, 300)}

held = set()
for l in open(os.path.join(BASE, "..", "datasets", "heldout", "heldout-v1.jsonl")):
    if l.strip():
        held.add(json.loads(l)["state"].strip().lower())
v03 = set()
for fn in ["choice", "risk", "ranking", "scoring", "multicriteria", "confidence", "abstention", "benchmark"]:
    p = os.path.join(BASE, "..", "datasets", "expanded-v2", f"{fn}.jsonl")
    if os.path.exists(p):
        for l in open(p):
            if l.strip():
                v03.add(json.loads(l)["state"].strip().lower())

manifest = {"seed": 44, "source": "template-expansion-v0.4", "license": "CC-BY-4.0", "files": {}}
for cat, (fn, n) in G.items():
    recs, seen = [], set()
    for r in fn(n):
        key = r["state"].strip().lower()
        if key in seen or key in held or key in v03:
            continue
        seen.add(key)
        recs.append(r)
    for j, r in enumerate(recs):
        r["id"] = f"BH-D4-{cat}-{j:04d}"
    path = os.path.join(OUT, f"{cat}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    manifest["files"][cat] = {"n": len(recs), "sha256": h}
    print(cat, len(recs))
manifest["total"] = sum(v["n"] for v in manifest["files"].values())
json.dump(manifest, open(os.path.join(OUT, "manifest-v0.4.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", manifest["total"])
