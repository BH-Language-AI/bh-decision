#!/usr/bin/env python3
"""Question-sweep: 3 formulacije pitanja x (stock, v4) kroz readout, held-out v1.
CPU. Izlaz: datasets/selfdistill/readout-qsweep.jsonl
"""
import json
import os
import time

MODELS = {"stock": "morriszjm/Tacit-4B", "v4": "/tmp/opencode/merged-v4"}
QS = {
    "q1": {"bs": "Koji je najbolji odgovor?", "en": "Which is the best option?"},
    "q2": None,  # state kao pitanje
    "q3": {"bs": "Šta je najbolji sljedeći korak?", "en": "What is the best next step?"},
}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "selfdistill")
os.makedirs(OUT, exist_ok=True)

held = [json.loads(l) for l in open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets",
                 "heldout", "heldout-v1.jsonl")) if l.strip()]
items = [(h["id"], h["state"], [(o["id"], o["text"]) for o in h["options"]],
          h["reference"]["decision"] if h.get("reference") else None,
          h.get("lang", "bs"))
         for h in held if h.get("options") and len(h.get("options", [])) >= 2]

from anyjev import Tacit  # noqa: E402

allrecs = []
for label, mid in MODELS.items():
    if os.path.isabs(mid) or mid.startswith((".", "/tmp")):
        assert os.path.exists(mid), mid
    tacit = Tacit.from_pretrained(mid, adaptive=False)
    for qtag, q in QS.items():
        for hid, state, opts, exp, lang in items:
            t2id = {t: i for i, t in opts}
            question = state if q is None else q.get(lang, q["bs"])
            try:
                d = tacit.decide(state=state, question=question,
                                 options=[t for _, t in opts], kind="choice")
                got = t2id.get(d["answer"])
                rec = {"model": label, "q": qtag, "id": hid, "expected": exp,
                       "answer_id": got,
                       "correct": (str(got) == str(exp)) if (exp and got) else None}
            except Exception as e:  # noqa: BLE001
                rec = {"model": label, "q": qtag, "id": hid, "error": str(e)[:120]}
            allrecs.append(rec)
            print(json.dumps({"model": label, "q": qtag, "id": hid,
                              "correct": rec.get("correct")}), flush=True)
    del tacit
with open(os.path.join(OUT, "readout-qsweep.jsonl"), "w") as f:
    for r in allrecs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
for m in MODELS:
    for q in QS:
        rs = [r for r in allrecs if r["model"] == m and r["q"] == q and r.get("correct") is not None]
        print(f"{m}/{q}: {sum(1 for r in rs if r['correct'])}/{len(rs)}", flush=True)
