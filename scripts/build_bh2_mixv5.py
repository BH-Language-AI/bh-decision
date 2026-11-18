#!/usr/bin/env python3
"""BH-Decision-2 mix v5: ODLUČUJUĆI eksperiment — potpuni balans o1/o2/o3.
Šablonski o1/o2 se subsamplaju na nivo o3 (~778); human + ostale kategorije cijele.
Ako balansiran model drži stock nivo bez defaulta → podaci imaju smisla.
Ako padne na chance → kraj SFT-a na šablonima. Seed 7.
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


def dec(r):
    try:
        return json.loads(r["text"].split("ODLUKA: ", 1)[1]).get("decision")
    except Exception:
        return None


by_dec = {}
for r in recs:
    by_dec.setdefault(dec(r), []).append(r)
print("prije:", {k: len(v) for k, v in by_dec.items()})
target = min(len(by_dec.get("o1", [])), len(by_dec.get("o2", [])),
             len(by_dec.get("o3", [])))
print("cilj po klasi:", target)
final = []
for k, v in by_dec.items():
    if k in ("o1", "o2", "o3") and len(v) > target:
        final += R.sample(v, target)
    else:
        final += v


def is_en(text):
    return bool(re.fullmatch(r"[ -\~\n\r\t]*", text.split("\n")[0]))


R.shuffle(final)
with open(os.path.join(OUTD, "train-v5.jsonl"), "w", encoding="utf-8") as f:
    for r in final:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUTD, "train-v5.jsonl"), "rb").read()).hexdigest()[:16]
dist = dict(Counter(dec(r) for r in final))
en = sum(1 for r in final if is_en(r["text"]))
json.dump({"seed": 7, "n": len(final), "sha256": h, "izvor": "train-v4 balansiran o1=o2=o3",
           "decision_distribucija": dist,
           "en_udio_grubo": round(en / len(final), 3)},
          open(os.path.join(OUTD, "manifest-v5.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(final), "dist:", dist, "en~", round(en / len(final), 3))
