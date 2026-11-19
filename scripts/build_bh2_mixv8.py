#!/usr/bin/env python3
"""BH-Decision-2 mix v8: train-v7 (5529) + kontrolna doza eksternog (1000 CSQA + 1000 ETHICS).
Prvi test da li eksterni EN uopste pomaze held-outu. Mala doza da ne razvodni bs signal.
Seed 7. Cilj: usporedba s v7 baselineom (gen 7/19, readout 15/19).
"""
import glob
import hashlib
import json
import os
import random
import re
from collections import Counter

R = random.Random(7)
HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(HERE, "..", "datasets", "bh-decision-2")
EXTD = os.path.join(HERE, "..", "datasets", "external")
KEEP = {"decision", "options_ranked", "scores", "risk", "confidence",
        "abstention_reason", "rationale_short", "rationale_full"}

recs = [json.loads(l) for l in
        open(os.path.join(OUTD, "train-v7.jsonl"), encoding="utf-8") if l.strip()]
print("train-v7:", len(recs))

ext = []
for fn in ["ext-csqa.jsonl", "ext-qasc.jsonl", "ethics-commonsense-train.jsonl", "ethics-justice-train.jsonl"]:
    p = os.path.join(EXTD, fn)
    if not os.path.exists(p):
        # fallback: prefiksi iz build skripti
        cands = glob.glob(os.path.join(EXTD, "*.jsonl"))
        print("nedostaje", fn, "| ima:", [os.path.basename(c) for c in cands])
        continue
    for l in open(p, encoding="utf-8"):
        if l.strip():
            ext.append(json.loads(l))
print("eksterni pool:", len(ext))


def key(r):
    if r.get("source", "").startswith("qasc") or "QASC" in r.get("id", ""):
        return "qasc"
    if "CSQA" in r.get("id", ""):
        return "csqa"
    return "ethics"


by_src = {}
for r in ext:
    by_src.setdefault(key(r), []).append(r)
print("po izvoru:", {k: len(v) for k, v in by_src.items()})

dose = []
dose += R.sample(by_src.get("csqa", []), min(1000, len(by_src.get("csqa", []))))
eth = by_src.get("ethics", [])
dose += R.sample(eth, min(1000, len(eth)))
print("doza:", len(dose))

for r in dose:
    ref = {k: v for k, v in r["reference"].items() if k in KEEP}
    recs.append({"text": (r.get("state", "") + "\nODLUKA: "
                          + json.dumps(ref, ensure_ascii=False))})


def dec(r):
    try:
        d = json.loads(r["text"].split("ODLUKA: ", 1)[1]).get("decision")
        return str(d) if isinstance(d, list) else d
    except Exception:
        return None


def is_en(text):
    return bool(re.fullmatch(r"[ -\~\n\r\t]*", text.split("\n")[0]))


R.shuffle(recs)
with open(os.path.join(OUTD, "train-v8.jsonl"), "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUTD, "train-v8.jsonl"), "rb").read()).hexdigest()[:16]
dist = dict(Counter(dec(r) for r in recs))
en = sum(1 for r in recs if is_en(r["text"]))
json.dump({"seed": 7, "n": len(recs), "sha256": h, "izvor": "train-v7 + 1k CSQA + 1k ETHICS",
           "decision_distribucija": dist,
           "en_udio_grubo": round(en / len(recs), 3)},
          open(os.path.join(OUTD, "manifest-v8.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(recs), "dist:", {k: dist[k] for k in list(dist)[:8]}, "en~", round(en / len(recs), 3))
