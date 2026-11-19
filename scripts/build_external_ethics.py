#!/usr/bin/env python3
"""ETHICS moralni sudovi -> nas format (yes_no). Samo train splitovi.
commonsense: label 0=moralno OK -> Da; 1=pogresno -> Ne (provjereno uzorcima).
justice: label 1=razuman zahtjev -> Da; 0=nerazuman -> Ne (provjereno uzorcima).
deontology/virtue PRESKOCENO: nedostaje excuse kontekst / nejasna semantika osobine.
Licenca: MIT (Hendrycks et al.; konverzija tasksource). Atribucija u README kartici.
"""
import hashlib
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "external")
os.makedirs(OUT, exist_ok=True)

from datasets import load_dataset  # noqa: E402

JOBS = [
    ("tasksource/ethics", "commonsense",
     "Da li je postupak moralan?",
     {0: "yes", 1: "no"}, "ethics-commonsense-train"),
    ("tasksource/ethics", "justice",
     "Da li je zahtjev razuman?",
     {1: "yes", 0: "no"}, "ethics-justice-train"),
]

total, h = 0, hashlib.sha256()
per = {}
for ds, cfg, q_en, mapping, prefix in JOBS:
    recs = []
    for i, r in enumerate(load_dataset(ds, cfg, split="train")):
        lab = int(r["label"])
        if lab not in mapping:
            continue
        yn = mapping[lab]
        opts = [{"id": "yes", "text": "Yes"}, {"id": "no", "text": "No"}]
        recs.append({
            "id": f"EXT-{prefix.split('-')[1][:3].upper()}-{i:05d}",
            "lang": "en", "state": str(r["text"]),
            "question": q_en, "options": opts,
            "reference": {"decision": yn, "options_ranked": [yn],
                          "scores": {"yes": 1.0 if yn == "yes" else 0.0,
                                     "no": 1.0 if yn == "no" else 0.0},
                          "risk": {"level": "low", "factors": []}, "confidence": 1.0,
                          "abstention_reason": None, "rationale_short": None},
            "source": prefix, "license": "MIT"})
    with open(os.path.join(OUT, f"{prefix}.jsonl"), "w") as f:
        for r in recs:
            line = json.dumps(r, ensure_ascii=False)
            f.write(line + "\n")
            h.update(line.encode())
    per[prefix] = len(recs)
    total += len(recs)
    print(prefix, len(recs), flush=True)
json.dump({"seed": 0, "n": total, "sha256": h.hexdigest()[:16], "sastav": per,
           "napomena": "ETHICS train; deontology/virtue preskoceni (nepotpun kontekst)"},
          open(os.path.join(OUT, "manifest-external-ethics.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", total)
