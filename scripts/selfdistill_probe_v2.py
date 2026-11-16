#!/usr/bin/env python3
"""Korak-2 proba v2: state-specific opcije (popravak dizajn-greške v1).
Svaka situacija ima 3 konkretne opcije s namjeravanim najboljim odgovorom.
Cilj: (a) distribucija odgovora nije konstantna, (b) slaganje s namjerom,
(c) cot route udio. CPU ~2-5 min/stavci — pokrenuti u pozadini.
Izlaz: datasets/selfdistill/probe-v2.jsonl
"""
import json
import os
import time

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "selfdistill")
os.makedirs(OUT, exist_ok=True)

# (state, question, [o1, o2, o3], expected_index) — o1/o2/o3 redom bez otkrivanja tačnog
CASES = [
    ("Komšija nudi da ti čuva ključeve stana dok si na odmoru, iako ga jedva poznaješ.",
     "Šta je najsigurnije?",
     ["Dati ključeve komšiji bez rezerve.", "Dati ključeve pouzdanom rođaku i javiti komšiji da je stan nadziran.", "Ostaviti ključ pod otiračem za svaki slučaj."],
     1),
    ("Prodavac polovnog frižidera tvrdi da je 'kao nov', ali ne daje garanciju ni račun.",
     "Šta je najbolji prvi korak?",
     ["Platiti odmah punu cijenu.", "Tražiti probni rad i pisani dogovor ili odustati.", "Platiti kaparu bez ikakvog papira."],
     1),
    ("Dijete se žali na jak bol u uhu usred noći, apoteka zatvorena do jutra.",
     "Šta je najrazumnije?",
     ["Čekati do jutra bez ikakve pomoći.", "Umiriti dijete, pratiti simptome i zvati dežurnog ljekara za savjet.", "Dati djetetu antibiotik koji je ostao od odraslog."],
     1),
    ("Šef nudi prekovremeni rad plaćen 'na ruke', bez evidencije.",
     "Šta je najsigurnija opcija?",
     ["Prihvatiti bez pitanja.", "Tražiti pisanu evidenciju i zakonitu isplatu.", "Odbaciti posao i dati otkaz odmah."],
     1),
    ("Na pijaci prodavac vaga voće na sumnjivoj vagi koja pokazuje više nego što izgleda.",
     "Šta bi uradila oprezna osoba?",
     ["Platiti bez riječi.", "Ljubazno tražiti provjeru na drugoj vagi ili odustati od kupovine.", "Optužiti prodavca za krađu pred svima."],
     1),
    ("Stanar u zgradi ostavlja smeće na hodniku danima, miris se širi.",
     "Šta je najbolji prvi korak?",
     ["Baciti njegovo smeće kroz prozor.", "Upozoriti ga mirno, pa prijaviti upravniku ako se ponovi.", "Ignorisati i preseliti se."],
     1),
    ("Prijatelj te nagovara da uložiš ušteđevinu u 'siguran' kripto projekat koji obećava duplu zaradu za mjesec.",
     "Šta je najrazumnije?",
     ["Uložiti svu ušteđevinu odmah.", "Ne ulagati bez provjere; ponuda s garantovanom duplom zaradom je znak prevare.", "Posuditi novac pa uložiti i posuđeno."],
     1),
    ("Vozač ispred tebe na semaforu ne kreće na zeleno, vjerovatno gleda u telefon.",
     "Šta je najbolji prvi korak?",
     ["Trubiti dugo i izaći se svađati.", "Kratko signalizirati i sačekati; ako ne reaguje, oprezno obići kad je sigurno.", "Proći kroz crveno da ga prestigneš."],
     1),
    ("U školi dijete dobija loše ocjene iz matematike, učitelj predlaže privatne časove kod njega za novac.",
     "Šta je najrazumnije?",
     ["Platiti bez pitanja.", "Provjeriti napredak s drugim učiteljem i pravila škole o sukobu interesa.", "Prebaciti dijete u drugu školu odmah."],
     1),
    ("Gost u kafani pronalazi stranu stvar u piću.",
     "Šta bi uradila oprezna osoba?",
     ["Popiti do kraja da ne pravi scenu.", "Vratiti piće i tražiti zamjenu, mirno upozoriti osoblje.", "Razbiti čašu i tražiti besplatno piće cijelu noć."],
     1),
    ("Firma kasni s platom treći mjesec, šef obećava 'sve odjednom uskoro' ali bez datuma.",
     "Šta je najbolji prvi korak?",
     ["Dati otkaz istog dana bez plana.", "Tražiti pisani rok isplate i raspitati se o pravima radnika.", "Raditi duplo više da se šef smiluje."],
     1),
    ("Na vratima se pojavljuje 'majstor' koji nudi hitnu popravku krova jer je 'vidio oštećenje', traži avans u gotovini.",
     "Šta je najsigurnije?",
     ["Dati avans odmah dok je tu.", "Ne davati novac nepozvanom ponuđaču; provjeriti krov nezavisno.", "Potpisati ugovor bez čitanja da ga ne uvrijediš."],
     1),
]

from anyjev import Tacit  # noqa: E402

tacit = Tacit.from_pretrained("morriszjm/Tacit-4B", adaptive=True, tau=0.5,
                              max_cot_share=0.5, cot_window=100, cot_max_tokens=1024)
recs = []
for i, (state, q, opts, exp) in enumerate(CASES):
    t0 = time.time()
    try:
        d = tacit.decide(state=state, question=q, options=opts, kind="choice")
        rec = {"id": f"SD-002-{i:02d}", "state": state, "question": q,
               "options": opts, "expected": opts[exp],
               "answer": d["answer"], "probs": {str(k): float(v) for k, v in d["probs"].items()},
               "route": d.get("route"), "latency_s": round(time.time() - t0, 1)}
    except Exception as e:  # noqa: BLE001
        rec = {"id": f"SD-002-{i:02d}", "state": state, "error": str(e)[:200]}
    recs.append(rec)
    print(json.dumps({"id": rec["id"], "answer": rec.get("answer"), "expected": rec.get("expected"),
                      "route": rec.get("route"), "latency_s": rec.get("latency_s"),
                      "error": rec.get("error")}, ensure_ascii=False), flush=True)

with open(os.path.join(OUT, "probe-v2.jsonl"), "w") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
ok = sum(1 for r in recs if r.get("answer") == r.get("expected"))
cot = sum(1 for r in recs if r.get("route") == "cot")
from collections import Counter
dist = Counter(r.get("answer") for r in recs if "answer" in r)
print(f"GOTOVO: {len(recs)} stavki, pogodak={ok}/{len(recs)}, cot={cot}, distribucija={dict(dist)}", flush=True)
