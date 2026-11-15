#!/usr/bin/env python3
"""Balansirani trening-miks v1: v0.4 + v0.5 cijeli, v0.3 subsample da o1 ne dominira.
Cilj po odluci: ~600 (o1/o2/o3), abstain sve, ranking kanali prirodno.
Deterministički (seed 7), manifest s hash. CC-BY-4.0.
"""
import glob
import hashlib
import json
import os
import random

R = random.Random(7)
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "datasets", "train-mix-v1")
os.makedirs(OUT, exist_ok=True)

pool = []
for pat in ["../datasets/expanded-v2/*.jsonl", "../datasets/expanded-v04/*.jsonl",
            "../datasets/expanded-v05/human-v05.jsonl"]:
    for f in sorted(glob.glob(os.path.join(BASE, pat))):
        cat = os.path.basename(f).replace(".jsonl", "")
        for l in open(f):
            if l.strip():
                r = json.loads(l)
                pool.append((cat, r))

by = {}
for cat, r in pool:
    key = (cat, str(r.get("reference", {}).get("decision")))
    by.setdefault(key, []).append(r)
human = [r for cat, r in pool if r.get("id", "").startswith("BH-D5-")]
bycat_human = {"human": human}

CAP = {"o1": 600, "o2": 600, "o3": 600}
mixed = []
for (cat, dec), rs in sorted(by.items()):
    if dec in CAP and len(rs) > CAP[dec]:
        rs = R.sample(rs, CAP[dec])
    mixed.extend((cat, r) for r in rs)
R.shuffle(mixed)

bycat = {}
for cat, r in mixed:
    bycat.setdefault(cat, []).append(r)

manifest = {"seed": 7, "source": "train-mix-v1 (v0.3-subsample + v0.4 + v0.5)",
            "license": "CC-BY-4.0", "files": {}}
for cat, rs in sorted(bycat.items()):
    path = os.path.join(OUT, f"{cat}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in rs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    manifest["files"][cat] = {"n": len(rs),
                               "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]}
for hc, rs in bycat_human.items():
    path = os.path.join(OUT, f"{hc}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in rs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    manifest["files"][hc] = {"n": len(rs),
                              "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]}
manifest["total"] = sum(v["n"] for v in manifest["files"].values())
json.dump(manifest, open(os.path.join(OUT, "manifest-mix-v1.json"), "w"),
          ensure_ascii=False, indent=1)

from collections import Counter
print("UKUPNO:", manifest["total"])
print(Counter(str(r.get("reference", {}).get("decision")) for _, r in mixed))
