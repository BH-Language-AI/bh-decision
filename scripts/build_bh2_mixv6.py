#!/usr/bin/env python3
"""BH-Decision-2 mix v6: dedup train-v4 (normalizovana stanja, prvi ostaje) + 5 epoha run.
Posljednji template eksperiment s pre-registriranim krajem: ako readout i dalje
ne tuče stock 16/19 → trening se ne nastavlja bez human 10x (tim). Seed 7.
"""
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
        open(os.path.join(OUTD, "train-v4.jsonl"), encoding="utf-8") if l.strip()]
print("train-v4:", len(recs))


def norm_state(r):
    t = r["text"].split("\nODLUKA: ", 1)[0]
    return re.sub(r"\s+", " ", re.sub(r"\d+", "N", t)).strip().lower()


seen, final, dropped = set(), [], 0
for r in recs:
    k = norm_state(r)
    if k in seen:
        dropped += 1
        continue
    seen.add(k)
    final.append(r)


def dec(r):
    try:
        return json.loads(r["text"].split("ODLUKA: ", 1)[1]).get("decision")
    except Exception:
        return None


def is_en(text):
    return bool(re.fullmatch(r"[ -\~\n\r\t]*", text.split("\n")[0]))


R.shuffle(final)
with open(os.path.join(OUTD, "train-v6.jsonl"), "w", encoding="utf-8") as f:
    for r in final:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUTD, "train-v6.jsonl"), "rb").read()).hexdigest()[:16]
dist = dict(Counter(dec(r) for r in final))
en = sum(1 for r in final if is_en(r["text"]))
json.dump({"seed": 7, "n": len(final), "sha256": h, "izvor": "train-v4 dedup (prvi ostaje)",
           "izbaceno_duplikata": dropped,
           "decision_distribucija": dist,
           "en_udio_grubo": round(en / len(final), 3)},
          open(os.path.join(OUTD, "manifest-v6.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(final), "dist:", dist, "en~", round(en / len(final), 3), "van:", dropped)
