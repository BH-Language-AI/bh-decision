#!/usr/bin/env python3
"""Rucni readout scorer (bez Tacit ovisnosti): argmin NLL po opcijama.
Koristi se za arhitekture koje AutoModelForCausalLM ne mapira (Mistral3).
Validacija: isti scorer na vA mora dati 18/19 q1.
"""
import json
import os
import sys

import torch
from transformers import AutoModelForImageTextToText, AutoTokenizer
from peft import PeftModel


def load_merged(base, adapter, outdir, dtype=torch.float16):
    if not os.path.exists(os.path.join(outdir, "config.json")):
        print("MERGE-START", base, flush=True)
        tok = AutoTokenizer.from_pretrained(base)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        b = AutoModelForImageTextToText.from_pretrained(
            base, torch_dtype=dtype, low_cpu_mem_usage=True)
        m = PeftModel.from_pretrained(b, adapter)
        m.merge_and_unload().save_pretrained(outdir)
        tok.save_pretrained(outdir)
        del m, b
        print("MERGED", outdir, flush=True)
    tok = AutoTokenizer.from_pretrained(outdir)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    mdl = AutoModelForImageTextToText.from_pretrained(
        outdir, torch_dtype=dtype, low_cpu_mem_usage=True)
    mdl.eval()
    return tok, mdl


@torch.no_grad()
def option_nll(model, tok, prompt, option):
    full = prompt + " " + option
    enc_full = tok(full, return_tensors="pt")
    enc_prompt = tok(prompt, return_tensors="pt")
    ids = enc_full["input_ids"]
    plen = enc_prompt["input_ids"].shape[1]
    out = model(input_ids=ids)
    logp = torch.log_softmax(out.logits[0], dim=-1)
    tok_ids = ids[0][plen:]
    if len(tok_ids) == 0:
        return float("inf")
    nll = -logp[torch.arange(plen - 1, ids.shape[1] - 1), tok_ids].sum().item()
    return nll / len(tok_ids)


def score_model(model, tok, items, Q, label):
    import math
    recs = []
    for hid, state, opts, exp, lang in items:
        q = Q.get(lang, Q["bs"])
        prompt = f"Stanje: {state}\nPitanje: {q}\nOpcije:\n" + "\n".join(
            f"{o}: {t}" for o, t in opts)
        try:
            nlls = {t: option_nll(model, tok, prompt, t) for _, t in opts}
            best = min(nlls, key=nlls.get)
            mx = max(-v for v in nlls.values())
            exps = {k: math.exp(-v - mx) for k, v in nlls.items()}
            s = sum(exps.values())
            probs = {k: v / s for k, v in exps.items()}
            t2id = {t: i for i, t in opts}
            got = t2id.get(best)
            recs.append({"model": label, "id": hid, "expected": exp, "answer_id": got,
                         "probs": {str(k): float(v) for k, v in probs.items()},
                         "correct": (str(got) == str(exp)) if (exp and got) else None})
        except Exception as e:  # noqa: BLE001
            recs.append({"model": label, "id": hid, "error": str(e)[:200]})
        print(json.dumps({"model": label, "id": hid,
                          "correct": recs[-1].get("correct")}), flush=True)
    return recs


def load_items():
    held = [json.loads(l) for l in open(
        "/home/sha/BH-Decision/datasets/heldout/heldout-v1.jsonl") if l.strip()]
    return [(h["id"], h["state"], [(o["id"], o["text"]) for o in h["options"]],
             h["reference"]["decision"] if h.get("reference") else None,
             h.get("lang", "bs"))
            for h in held if h.get("options") and len(h.get("options", [])) >= 2]


if __name__ == "__main__":
    Q = {"bs": "Koji je najbolji odgovor?", "en": "Which is the best option?"}
    mode = sys.argv[1] if len(sys.argv) > 1 else "9b"
    items = load_items()
    allrecs = []
    if mode == "9b":
        BASE = "mistralai/Ministral-3-8B-Base-2512"
        for label, mid in [("stock-8b", None), ("bh2-9b", "/tmp/opencode/adapter-9b")]:
            if mid is None:
                tok = AutoTokenizer.from_pretrained(BASE)
                mdl = AutoModelForImageTextToText.from_pretrained(
                    BASE, torch_dtype=torch.float16, low_cpu_mem_usage=True)
                mdl.eval()
            else:
                tok, mdl = load_merged(BASE, mid, "/tmp/opencode/merged-9b")
            allrecs += score_model(mdl, tok, items, Q, label)
            del mdl
        out = "/home/sha/BH-Decision/datasets/selfdistill/readout-v9b.jsonl"
    else:  # validacija na vA s HF-a
        from huggingface_hub import snapshot_download
        ad = snapshot_download("BH-Language-AI/bh-decision-2-4b",
                               allow_patterns=["adapter_*"])
        tok, mdl = load_merged("morriszjm/Tacit-4B", ad, "/tmp/opencode/merged-vA2")
        allrecs = score_model(mdl, tok, items, Q, "bh2-vA-check")
        del mdl
        out = "/tmp/opencode/readout-vA-check.jsonl"
    with open(out, "w") as f:
        for r in allrecs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    for m in sorted(set(r["model"] for r in allrecs)):
        rs = [r for r in allrecs if r["model"] == m and r.get("correct") is not None]
        print(m, sum(1 for r in rs if r["correct"]), "/", len(rs),
              dict(Counter(r.get("answer_id") for r in rs)), flush=True)
    print("GOTOVO", out, flush=True)
