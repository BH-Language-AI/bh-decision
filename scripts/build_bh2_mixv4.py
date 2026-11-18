#!/usr/bin/env python3
"""BH-Decision-2 mix v4: train-v3 (5189) + human v07 (200) + ČIŠĆENJE targeta.
Svi targeti se svode na 7 ključeva (decision, options_ranked, scores, risk,
confidence, abstention_reason, rationale_short) — van: lang/model/version
metadata koje je v3 model papagajisao u izlaz. Deterministički, seed 7.
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
KEEP = {"decision", "options_ranked", "scores", "risk", "confidence",
        "abstention_reason", "rationale_short"}
stripped = 0

recs = []
for l in open(os.path.join(OUTD, "train-v3.jsonl"), encoding="utf-8"):
    if l.strip():
        recs.append(json.loads(l))
print("train-v3:", len(recs))
n_v07 = 0
for put in sorted(glob.glob(os.path.join(HERE, "..", "datasets", "expanded-v07", "*.jsonl"))):
    for l in open(put, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        recs.append({"text": r["state"] + "\nODLUKA: " + json.dumps(r["reference"], ensure_ascii=False)})
        n_v07 += 1
print("v07:", n_v07)


def clean(r):
    global stripped
    head, sep, tail = r["text"].partition("\nODLUKA: ")
    try:
        d = json.loads(tail)
    except Exception:
        return r
    if set(d) - KEEP:
        stripped += 1
        d = {k: d.get(k) for k in KEEP}
        r["text"] = head + sep + json.dumps(d, ensure_ascii=False)
    return r


recs = [clean(r) for r in recs]


def dec(r):
    try:
        return json.loads(r["text"].split("ODLUKA: ", 1)[1]).get("decision")
    except Exception:
        return None


def is_en(text):
    return bool(re.fullmatch(r"[ -\~\n\r\t]*", text.split("\n")[0]))


R.shuffle(recs)
with open(os.path.join(OUTD, "train-v4.jsonl"), "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUTD, "train-v4.jsonl"), "rb").read()).hexdigest()[:16]
dist = dict(Counter(dec(r) for r in recs))
en = sum(1 for r in recs if is_en(r["text"]))
json.dump({"seed": 7, "n": len(recs), "sha256": h, "izvor": "train-v3 + human-v07 (200)",
           "ociscenih_targeta": stripped,
           "decision_distribucija": dist,
           "en_udio_grubo": round(en / len(recs), 3)},
          open(os.path.join(OUTD, "manifest-v4.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(recs), "dist:", dist, "en~", round(en / len(recs), 3), "ocisceno:", stripped)
