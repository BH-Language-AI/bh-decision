#!/usr/bin/env python3
"""Eksterni EN pool: commonsense_qa (MIT) + allenai/qasc (CC-BY-4.0) -> naš format.
Samo train splitovi, atribucija u README kartici + source polju svake stavke.
Lokalno: datasets/external/<ime>/pool.jsonl + manifest-external.json
"""
import hashlib
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "external")
os.makedirs(OUT, exist_ok=True)

from datasets import load_dataset  # noqa: E402


def conv(rows, prefix, source, lic):
    out = []
    for i, r in enumerate(rows):
        try:
            ch = r["choices"]
            labels = list(ch["label"])
            texts = list(ch["text"])
            key = str(r["answerKey"]).strip().upper()
            idx = labels.index(key)
        except Exception:
            continue
        opts = [{"id": f"o{j+1}", "text": t} for j, t in enumerate(texts)]
        dec = f"o{idx+1}"
        out.append({
            "id": f"{prefix}-{i:05d}", "lang": "en", "state": str(r["question"]),
            "options": opts,
            "reference": {"decision": dec, "options_ranked": [dec],
                          "scores": {o["id"]: (1.0 if o["id"] == dec else 0.0) for o in opts},
                          "risk": {"level": "low", "factors": []}, "confidence": 1.0,
                          "abstention_reason": None,
                          "rationale_short": None, "rationale_source": "gold-human"},
            "source": source, "license": lic})
    return out


jobs = [("tau/commonsense_qa", None, "EXT-CSQA", "commonsenseqa-train", "MIT"),
        ("allenai/qasc", None, "EXT-QASC", "qasc-train", "CC-BY-4.0")]
total, h = 0, hashlib.sha256()
per = {}
for ds, cfg, prefix, src, lic in jobs:
    rows = list(load_dataset(ds, cfg or None, split="train"))
    recs = conv(rows, prefix, src, lic)
    with open(os.path.join(OUT, f"{prefix.lower()}.jsonl"), "w") as f:
        for r in recs:
            line = json.dumps(r, ensure_ascii=False)
            f.write(line + "\n")
            h.update(line.encode())
    per[prefix] = len(recs)
    total += len(recs)
    print(prefix, len(recs), flush=True)
json.dump({"seed": 0, "n": total, "sha256": h.hexdigest()[:16],
           "sastav": per, "napomena": "samo train splitovi; atribucija u README kartici"},
          open(os.path.join(OUT, "manifest-external.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", total)
