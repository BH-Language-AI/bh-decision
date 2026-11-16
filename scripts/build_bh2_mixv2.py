#!/usr/bin/env python3
"""BH-Decision-2 mix v2: samo JSON ciljevi (šabloni + human), bez think-tragova,
bez bosnian-core spama, o2 prior srezan subsampleom na nivo o1. Deterministički.
Ulaz: datasets/bh-decision-2/train.jsonl (v1). Izlaz: train-v2.jsonl + manifest-v2.json.
Dijagnoza: docs/training/bh-decision-2-v1-2026-11-16.md
"""
import hashlib
import json
import os
import random

R = random.Random(7)
HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "..", "datasets", "bh-decision-2", "train.jsonl")
OUTD = os.path.join(HERE, "..", "datasets", "bh-decision-2")
OUT = os.path.join(OUTD, "train-v2.jsonl")

recs = [json.loads(l) for l in open(IN, encoding="utf-8") if l.strip()]
n_in = len(recs)

# 1) samo JSON ciljevi — van: think-tragovi i slobodni tekst (bosnian-core)
kept = [r for r in recs if "ODLUKA: {" in r["text"] and "<think>" not in r["text"]]
n_dropped_nonjson = n_in - len(kept)

# 2) o2 subsample na nivo o1 (prior kontrola)
def dec(r):
    try:
        return json.loads(r["text"].split("ODLUKA: ", 1)[1]).get("decision")
    except Exception:
        return None

by_dec = {}
for r in kept:
    by_dec.setdefault(dec(r), []).append(r)
n_o1 = len(by_dec.get("o1", []))
o2 = by_dec.get("o2", [])
n_o2_drop = 0
if len(o2) > n_o1:
    drop = set(R.sample(range(len(o2)), len(o2) - n_o1))
    by_dec["o2"] = [r for i, r in enumerate(o2) if i not in drop]
    n_o2_drop = len(drop)

final = [r for v in by_dec.values() for r in v]
R.shuffle(final)

with open(OUT, "w", encoding="utf-8") as f:
    for r in final:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
from collections import Counter
dist = dict(Counter(dec(r) for r in final))
json.dump({"seed": 7, "n": len(final), "sha256": h, "izvor": "train.jsonl v1 filtriran",
           "izbaceno_nejson": n_dropped_nonjson, "o2_subsample_drop": n_o2_drop,
           "decision_distribucija": dist},
          open(os.path.join(OUTD, "manifest-v2.json"), "w"), ensure_ascii=False, indent=1)
print(f"ulaz {n_in} -> izlaz {len(final)} (ne-json van: {n_dropped_nonjson}, o2 van: {n_o2_drop})")
print("distribucija:", dist)
