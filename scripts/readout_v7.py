#!/usr/bin/env python3
"""v6 readout: merge + 20 held-out itema kroz joint head (q1). Izlaz u readout-v7.jsonl."""
import json
import os
import time

BASE = "morriszjm/Tacit-4B"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "selfdistill")

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402
from peft import PeftModel  # noqa: E402

merged = "/tmp/opencode/merged-v7"
if not os.path.exists(os.path.join(merged, "config.json")):
    tok = AutoTokenizer.from_pretrained(BASE)
    base = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float16, low_cpu_mem_usage=True)
    model = PeftModel.from_pretrained(base, "/tmp/opencode/adapters/v7")
    model.merge_and_unload().save_pretrained(merged)
    tok.save_pretrained(merged)
    print("MERGED SPREMLJEN", flush=True)

held = [json.loads(l) for l in open(os.path.join(OUT, "..", "heldout", "heldout-v1.jsonl")) if l.strip()]
items = [(h["id"], h["state"], [(o["id"], o["text"]) for o in h["options"]],
          h["reference"]["decision"] if h.get("reference") else None, h.get("lang", "bs"))
         for h in held if h.get("options") and len(h.get("options", [])) >= 2]
Q = {"bs": "Koji je najbolji odgovor?", "en": "Which is the best option?"}

from anyjev import Tacit  # noqa: E402
tacit = Tacit.from_pretrained(merged, adaptive=False)
recs = []
for hid, state, opts, exp, lang in items:
    t2id = {t: i for i, t in opts}
    try:
        d = tacit.decide(state=state, question=Q.get(lang, Q["bs"]),
                         options=[t for _, t in opts], kind="choice")
        got = t2id.get(d["answer"])
        recs.append({"model": "bh2-v7", "id": hid, "expected": exp, "answer_id": got,
                     "correct": (str(got) == str(exp)) if (exp and got) else None})
    except Exception as e:  # noqa: BLE001
        recs.append({"model": "bh2-v7", "id": hid, "error": str(e)[:120]})
    print(json.dumps({"id": hid, "correct": recs[-1].get("correct")}), flush=True)
with open(os.path.join(OUT, "readout-v7.jsonl"), "w") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
rs = [r for r in recs if r.get("correct") is not None]
print(f"bh2-v7: {sum(1 for r in rs if r['correct'])}/{len(rs)}", flush=True)
