#!/usr/bin/env python3
"""Adapter readout test: da li je LoRA pokvario backbone ili samo generaciju?
Stock vs v4 vs v5 — SVI kroz isti AnyJev Tacit readout (one_forward) na held-out v1.
CPU ~1-2 min/stavci po modelu. Izlaz: datasets/selfdistill/readout-v45.jsonl
"""
import json
import os
import time

BASE = "morriszjm/Tacit-4B"
AD = "/tmp/opencode/adapters"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "selfdistill")
os.makedirs(OUT, exist_ok=True)

held = [json.loads(l) for l in open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets",
                 "heldout", "heldout-v1.jsonl")) if l.strip()]
items = [(h["id"], h["state"], [(o["id"], o["text"]) for o in h["options"]],
          h["reference"]["decision"] if h.get("reference") else None,
          h.get("lang", "bs"))
         for h in held if h.get("options") and len(h.get("options", [])) >= 2]

Q = {"bs": "Koji je najbolji odgovor?", "en": "Which is the best option?"}


def run_model(model_id, label):
    from anyjev import Tacit  # noqa: E402
    tacit = Tacit.from_pretrained(model_id, adaptive=False)
    recs = []
    for hid, state, opts, exp, lang in items:
        t2id = {t: i for i, t in opts}
        t0 = time.time()
        try:
            d = tacit.decide(state=state, question=Q.get(lang, Q["bs"]),
                             options=[t for _, t in opts], kind="choice")
            got = t2id.get(d["answer"])
            recs.append({"model": label, "id": hid, "expected": exp,
                         "answer": d["answer"], "answer_id": got,
                         "probs": {str(k): float(v) for k, v in d["probs"].items()},
                         "correct": (str(got) == str(exp)) if (exp and got) else None,
                         "latency_s": round(time.time() - t0, 1)})
        except Exception as e:  # noqa: BLE001
            recs.append({"model": label, "id": hid, "error": str(e)[:200]})
        print(json.dumps({"model": label, "id": recs[-1]["id"],
                          "correct": recs[-1].get("correct")}), flush=True)
    del tacit
    return recs


def merged_path(tag):
    """Spoji LoRA u bazu (fp16) i vrati putanju; preskoči ako postoji."""
    import torch  # noqa: E402
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402
    from peft import PeftModel  # noqa: E402
    out = f"/tmp/opencode/merged-{tag}"
    if os.path.exists(os.path.join(out, "config.json")):
        print(f"MERGED POSTOJI: {out}", flush=True)
        return out
    tok = AutoTokenizer.from_pretrained(BASE)
    base = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float16,
                                                low_cpu_mem_usage=True)
    model = PeftModel.from_pretrained(base, os.path.join(AD, tag))
    merged = model.merge_and_unload()
    merged.save_pretrained(out)
    tok.save_pretrained(out)
    del merged, model, base
    print(f"MERGED SPREMLJEN: {out}", flush=True)
    return out


allrecs = []
allrecs += run_model(BASE, "stock")
for tag in ["v4", "v5"]:
    allrecs += run_model(merged_path(tag), f"bh2-{tag}")
with open(os.path.join(OUT, "readout-v45.jsonl"), "w") as f:
    for r in allrecs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
from collections import Counter
for m in ["stock", "bh2-v4", "bh2-v5"]:
    rs = [r for r in allrecs if r["model"] == m and r.get("correct") is not None]
    print(f"{m}: {sum(1 for r in rs if r['correct'])}/{len(rs)} tacno, "
          f"dist={dict(Counter(r['answer'] for r in rs if 'answer' in r))}", flush=True)
