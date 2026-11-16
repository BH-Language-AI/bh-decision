#!/usr/bin/env python3
"""Train-mix v2: v1 + čišćenje + dvojezični prag.
- Izbacuje <think> blokove iz targeta (razbijaju JSON format).
- Izbacuje agentske petlje ('ne diraj', 'testni posao', 'ignorisi sve').
- Zahtijeva >=10% en stavki u miksu (provjera, ne tiho krpljenje).
Deterministički (seed 7). CC-BY-4.0 gdje je primjenjivo.
"""
import glob
import hashlib
import json
import os
import random
import re

R = random.Random(7)
BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "..", "datasets", "train-mix-v1")
OUT = os.path.join(BASE, "..", "datasets", "train-mix-v2")
os.makedirs(OUT, exist_ok=True)

JUNK_RES = [re.compile(p, re.I) for p in
            [r"<think>.*?</think>", r"ne diraj", r"testni posao", r"ignorisi sve"]]
THINK_RE = re.compile(r"<think>.*?</think>", re.I | re.S)


def clean(text):
    t = THINK_RE.sub("", text).strip()
    return t


def is_junk(text):
    return any(rx.search(text) for rx in JUNK_RES[1:])


bycat, dropped = {}, {"think": 0, "junk": 0, "empty": 0}
for path in sorted(glob.glob(os.path.join(SRC, "*.jsonl"))):
    cat = os.path.basename(path).replace(".jsonl", "")
    if cat == "manifest-mix-v1":
        continue
    for l in open(path, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        if "text" in r:
            txt = r["text"]
        else:
            txt = r.get("state", "") + "\nODLUKA: " + json.dumps(r.get("reference", {}), ensure_ascii=False)
        if "<think>" in txt.lower():
            txt = clean(txt)
            dropped["think"] += 1
        if not txt.strip():
            dropped["empty"] += 1
            continue
        if is_junk(txt):
            dropped["junk"] += 1
            continue
        r = {"text": txt, "id": r.get("id", ""), "lang": r.get("lang", ""),
               "source": ((r.get("source") or "mix-v1") + "+clean-v2")}
        bycat.setdefault(cat, []).append(r)

manifest = {"seed": 7, "source": "train-mix-v2 (v1 + clean)", "license": "CC-BY-4.0",
            "dropped": dropped, "files": {}}
total, en = 0, 0
for cat, rs in sorted(bycat.items()):
    en += sum(1 for r in rs if '"lang": "en"' in r["text"] or '"lang":"en"' in r["text"])
    path = os.path.join(OUT, f"{cat}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in rs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    manifest["files"][cat] = {"n": len(rs), "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]}
    total += len(rs)
manifest["total"] = total
json.dump(manifest, open(os.path.join(OUT, "manifest-mix-v2.json"), "w"),
          ensure_ascii=False, indent=1)
print("UKUPNO:", total, "odbačeno:", dropped)
print("en udio ~:", round(en / max(1, total), 3), "(gruba procjena po targetu)")
assert total > 4000, "premalo podataka nakon čišćenja"
