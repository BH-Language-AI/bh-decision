#!/usr/bin/env python3
"""BH-Decision-2 mix v3: train-v2 (4989, JSON-only) + human v06 (200, balansirano
o1 50/o2 50/o3 100, bs 100 + en 100). Deterministički, seed 7."""
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

recs = [json.loads(l) for l in
        open(os.path.join(OUTD, "train-v2.jsonl"), encoding="utf-8") if l.strip()]
print("train-v2:", len(recs))
n_v06 = 0
for put in sorted(glob.glob(os.path.join(HERE, "..", "datasets", "expanded-v06", "*.jsonl"))):
    for l in open(put, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        recs.append({"text": r["state"] + "\nODLUKA: " + json.dumps(r["reference"], ensure_ascii=False)})
        n_v06 += 1
print("v06:", n_v06)


def dec(r):
    try:
        return json.loads(r["text"].split("ODLUKA: ", 1)[1]).get("decision")
    except Exception:
        return None


def is_en(text):
    return bool(re.fullmatch(r"[ -\~\n\r\t]*", text.split("\n")[0]))


R.shuffle(recs)
with open(os.path.join(OUTD, "train-v3.jsonl"), "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUTD, "train-v3.jsonl"), "rb").read()).hexdigest()[:16]
dist = dict(Counter(dec(r) for r in recs))
en = sum(1 for r in recs if is_en(r["text"]))
json.dump({"seed": 7, "n": len(recs), "sha256": h, "izvor": "train-v2 + human-v06 (200)",
           "decision_distribucija": dist,
           "en_udio_grubo": round(en / len(recs), 3)},
          open(os.path.join(OUTD, "manifest-v3.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(recs), "dist:", dist, "en~", round(en / len(recs), 3))
