#!/usr/bin/env python3
"""Korak-2 proba: Tacit-4B generiše+odgovara 30 novih situacija (adaptive).
Cilj: vidjeti da li model proizvodi koherentan reasoning + stabilne odluke na
neviđenim temama. Izlaz: datasets/selfdistill/probe-v1.jsonl (state, reasoning, answer).
Sporo na CPU (~2-5 min/stavci) — pokrenuti u pozadini.
"""
import json
import os
import time

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "selfdistill")
os.makedirs(OUT, exist_ok=True)

SEEDS = [
    ("Kupiti polovan auto od nepoznatog prodavca koji ne da probnu vožnju.", ["o1", "o2", "o3"]),
    ("Stanodavac traži kiriju unaprijed za 6 mjeseci uz popust.", ["o1", "o2", "o3"]),
    ("Prijatelj traži da mu budeš žirant za kredit.", ["o1", "o2", "o3"]),
    ("Poslodavac nudi povišicu uz prelazak na noćne smjene.", ["o1", "o2", "o3"]),
    ("Škola traži saglasnost za ekskurziju u inostranstvo.", ["o1", "o2", "o3"]),
    ("Banka nudi kreditnu karticu s 'besplatnim' prvim godinama.", ["o1", "o2", "o3"]),
    ("Komšija gradi ogradu 30cm preko međe.", ["o1", "o2", "o3"]),
    ("Ljekar preporučuje skupi privatni pregled iako postoji besplatna alternativa.", ["o1", "o2", "o3"]),
    ("Prodavac na pijaci ne izdaje račun za veću kupovinu.", ["o1", "o2", "o3"]),
    ("Firma kasni s platom drugi mjesec zaredom.", ["o1", "o2", "o3"]),
    ("Dijete donosi lošu ocjenu i krije test.", ["o1", "o2", "o3"]),
    ("Auto se pregrijava na autoputu usred ljeta.", ["o1", "o2", "o3"]),
    ("Stanar primjećuje curenje plina u zgradi.", ["o1", "o2", "o3"]),
    ("Gost u restoranu nalazi muhu u supi.", ["o1", "o2", "o3"]),
    ("Radnik pronalazi novčanik na gradilištu.", ["o1", "o2", "o3"]),
    ("Studentu nude gotov diplomski rad za novac.", ["o1", "o2", "o3"]),
    ("Vozač udario parkirani auto i niko nije vidio.", ["o1", "o2", "o3"]),
    ("Pacijent čeka red 4 sata za hitan pregled.", ["o1", "o2", "o3"]),
    ("Prodavac odbija reklamaciju tehničke robe stare 5 dana.", ["o1", "o2", "o3"]),
    ("Komšijin pas laje cijelu noć.", ["o1", "o2", "o3"]),
    ("Firma nudi posao bez pismenog ugovora.", ["o1", "o2", "o3"]),
    ("Bankomat progutao karticu u petak navečer.", ["o1", "o2", "o3"]),
    ("Dijete progutalo novčić.", ["o1", "o2", "o3"]),
    ("Poplava u podrumu zgrade usred noći.", ["o1", "o2", "o3"]),
    ("Nestalo struje, frižider pun hrane, ljeto.", ["o1", "o2", "o3"]),
    ("Sumnjiva poruka od 'banke' traži PIN.", ["o1", "o2", "o3"]),
    ("Guma pukla na autoputu pri 120 km/h.", ["o1", "o2", "o3"]),
    ("Pas lutalica prati dijete kući.", ["o1", "o2", "o3"]),
    ("Poziv s nepoznatog broja: 'dobili ste nagradu'.", ["o1", "o2", "o3"]),
    ("Curenje vode sa plafona kod komšije ispod.", ["o1", "o2", "o3"]),
]

QUESTIONS = {
    "o1": "Šta je najbolji prvi korak?",
    "o2": "Šta je najsigurnija opcija?",
    "o3": "Šta bi uradila oprezna osoba?",
}

from anyjev import Tacit  # noqa: E402

tacit = Tacit.from_pretrained("morriszjm/Tacit-4B", adaptive=True, tau=0.5,
                              max_cot_share=0.5, cot_window=100, cot_max_tokens=1024)
recs = []
for i, (state, opts) in enumerate(SEEDS):
    q = QUESTIONS[["o1", "o2", "o3"][i % 3]]
    t0 = time.time()
    try:
        d = tacit.decide(state=state, question=q, options=["postupi odmah", "provjeri pa odluči", "odustani/prijavi"], kind="choice")
        rec = {"id": f"SD-001-{i:02d}", "state": state, "question": q,
               "answer": d["answer"], "probs": {str(k): float(v) for k, v in d["probs"].items()},
               "route": d.get("route"), "latency_s": round(time.time() - t0, 1)}
    except Exception as e:  # noqa: BLE001
        rec = {"id": f"SD-001-{i:02d}", "state": state, "error": str(e)[:200]}
    recs.append(rec)
    print(json.dumps({"id": rec["id"], "answer": rec.get("answer"), "route": rec.get("route"),
                      "latency_s": rec.get("latency_s"), "error": rec.get("error")}), flush=True)

with open(os.path.join(OUT, "probe-v1.jsonl"), "w") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
cot = sum(1 for r in recs if r.get("route") == "cot")
print(f"GOTOVO: {len(recs)} stavki, cot={cot}", flush=True)
