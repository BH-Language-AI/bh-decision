#!/usr/bin/env python3
"""BH-Decision-2 (Tacit linija) trening miks: šabloni (format) + thinking (tragovi) +
bosnian-core uzorak (jezik) + confirmation (sigurnost). Deterministički, manifest.
Bez Jev izlaza, bez tuđih decision-izlaza — samo naši + javni CC dataseti.
"""
import glob
import hashlib
import json
import os
import random

R = random.Random(7)
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "datasets", "bh-decision-2")
os.makedirs(OUT, exist_ok=True)

recs = []


def add_text(prompt, target):
    recs.append({"text": prompt + "\nODLUKA: " + target})


# 1) Naši šabloni (format sidro): state -> reference JSON
for pat in ["../datasets/train-mix-v1/*.jsonl"]:
    for put in sorted(glob.glob(os.path.join(BASE, pat))):
        for l in open(put, encoding="utf-8"):
            if not l.strip():
                continue
            r = json.loads(l)
            if "BH-D5-" in r.get("id", "") or "/human" in put:
                continue  # human ide odvojeno, bez capova
            add_text(r.get("state", ""), json.dumps(r.get("reference", {}), ensure_ascii=False))
# 1b) human stavke sve
for put in [os.path.join(BASE, "../datasets/train-mix-v1/human.jsonl"),
            os.path.join(BASE, "../datasets/expanded-v05/human-v05.jsonl")]:
    if os.path.exists(put):
        for l in open(put, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                add_text(r.get("state", ""), json.dumps(r.get("reference", {}), ensure_ascii=False))

# 2) HF dataseti (javni, CC): thinking + confirmation + bosnian-core uzorak
from huggingface_hub import hf_hub_download  # noqa: E402

def conv_chat(messages):
    u = next((m["content"] for m in messages if m.get("role") == "user"), "")
    a = next((m["content"] for m in messages if m.get("role") == "assistant"), "")
    return u, a

n_think = n_conf = n_core = 0
try:
    p = hf_hub_download("shaban2024/agentmujo-thinking", "thinking_v0.4.jsonl", repo_type="dataset")
    for l in open(p, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        u, a = conv_chat(r.get("messages", []))
        if u and a:
            add_text(u, a)
            n_think += 1
    print("thinking:", n_think)
except Exception as e:
    print("thinking SKIP:", str(e)[:120])

try:
    p = hf_hub_download("shaban2024/agentmujo-confirmation", "confirmation_v0.4.jsonl", repo_type="dataset")
    for l in open(p, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        u, a = conv_chat(r.get("messages", []))
        if u and a:
            add_text(u, a)
            n_conf += 1
    print("confirmation:", n_conf)
except Exception as e:
    print("confirmation SKIP:", str(e)[:120])

try:
    p = hf_hub_download("shaban2024/agentmujo-bosnian-core", "bosnian_core_v0.3.jsonl", repo_type="dataset")
    pool = []
    for l in open(p, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        u, a = conv_chat(r.get("messages", []))
        if u and a and len(a) < 2000:
            pool.append((u, a))
    for u, a in R.sample(pool, min(2000, len(pool))):
        add_text(u, a)
        n_core += 1
    print("bosnian-core uzorak:", n_core, "od", len(pool))
except Exception as e:
    print("bosnian-core SKIP:", str(e)[:120])

R.shuffle(recs)
with open(os.path.join(OUT, "train.jsonl"), "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUT, "train.jsonl"), "rb").read()).hexdigest()[:16]
json.dump({"seed": 7, "n": len(recs), "sha256": h,
           "sastav": {"templates": "train-mix-v1 bez human", "human": 200,
                      "thinking": n_think, "confirmation": n_conf, "bosnian_core": n_core}},
          open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(recs))
