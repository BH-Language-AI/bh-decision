#!/usr/bin/env python3
"""BH-Decision-2 mix v7: train-v4 (5389, čisti targeti) + v08 FULL (140).
v08 reasoning stavke ZADRŽAVAJU rationale_full (novi signal: učenje procesa, ne samo labela).
Multi-choice stavke imaju list-decision (harness ih ne boduje — dokumentovano).
Deterministički, seed 7.
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
        "abstention_reason", "rationale_short", "rationale_full"}

recs = [json.loads(l) for l in
        open(os.path.join(OUTD, "train-v4.jsonl"), encoding="utf-8") if l.strip()]
print("train-v4:", len(recs))
n_v08 = 0
for put in sorted(glob.glob(os.path.join(HERE, "..", "datasets", "expanded-v08", "*.jsonl"))):
    for l in open(put, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        ref = {k: v for k, v in r["reference"].items() if k in KEEP}
        recs.append({"text": r["state"] + "\nODLUKA: " + json.dumps(ref, ensure_ascii=False)})
        n_v08 += 1
print("v08:", n_v08)
with_rat = sum(1 for r in recs if "rationale_full" in r["text"])
print("sa rationale_full:", with_rat)


def dec(r):
    try:
        d = json.loads(r["text"].split("ODLUKA: ", 1)[1]).get("decision")
        return str(d) if isinstance(d, list) else d
    except Exception:
        return None


def is_en(text):
    return bool(re.fullmatch(r"[ -\~\n\r\t]*", text.split("\n")[0]))


R.shuffle(recs)
with open(os.path.join(OUTD, "train-v7.jsonl"), "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUTD, "train-v7.jsonl"), "rb").read()).hexdigest()[:16]
dist = dict(Counter(dec(r) for r in recs))
en = sum(1 for r in recs if is_en(r["text"]))
json.dump({"seed": 7, "n": len(recs), "sha256": h, "izvor": "train-v4 + v08 full (140)",
           "decision_distribucija": dist,
           "en_udio_grubo": round(en / len(recs), 3)},
          open(os.path.join(OUTD, "manifest-v7.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(recs), "dist:", dist, "en~", round(en / len(recs), 3))
