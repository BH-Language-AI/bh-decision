#!/usr/bin/env python3
"""BH-Decision-2 mix v10: train-v9 (7729) + v10 agent-draft (120, IZRICITO agent-assisted, NE human).
Test: da li agent-draft podaci pomiču held-out. Seed 7.
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
        open(os.path.join(OUTD, "train-v9.jsonl"), encoding="utf-8") if l.strip()]
print("train-v9:", len(recs))
n_v10 = 0
for put in sorted(glob.glob(os.path.join(HERE, "..", "datasets", "expanded-v10", "agent-draft-*.jsonl"))):
    for l in open(put, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        ref = {k: v for k, v in r["reference"].items() if k in KEEP}
        recs.append({"text": r["state"] + "\nODLUKA: " + json.dumps(ref, ensure_ascii=False),
                     "source": "agent-draft-v10"})
        n_v10 += 1
print("v10-draft:", n_v10)


def dec(r):
    try:
        d = json.loads(r["text"].split("ODLUKA: ", 1)[1]).get("decision")
        return str(d) if isinstance(d, list) else d
    except Exception:
        return None


def is_en(text):
    return bool(re.fullmatch(r"[ -\~\n\r\t]*", text.split("\n")[0]))


R.shuffle(recs)
with open(os.path.join(OUTD, "train-v10.jsonl"), "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUTD, "train-v10.jsonl"), "rb").read()).hexdigest()[:16]
dist = dict(Counter(dec(r) for r in recs))
en = sum(1 for r in recs if is_en(r["text"]))
json.dump({"seed": 7, "n": len(recs), "sha256": h, "izvor": "train-v9 + v10-draft (120 agent-assisted)",
           "decision_distribucija": dist,
           "en_udio_grubo": round(en / len(recs), 3)},
          open(os.path.join(OUTD, "manifest-v10.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(recs), "dist:", {k: dist[k] for k in list(dist)[:8]}, "en~", round(en / len(recs), 3))
