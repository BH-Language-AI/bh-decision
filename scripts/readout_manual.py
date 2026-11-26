#!/usr/bin/env python3
"""Rucni readout scorer (bez Tacit ovisnosti): argmin NLL po opcijama.
Koristi se za arhitekture koje AutoModelForCausalLM ne mapira (Mistral3).
Validacija: isti scorer na vA mora dati 18/19 q1.
"""
import json
import os
import sys

import torch
from transformers import (AutoConfig, AutoModelForCausalLM,
                          AutoModelForImageTextToText, AutoTokenizer)
from transformers.models.auto.modeling_auto import (
    MODEL_FOR_CAUSAL_LM_MAPPING, MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING)
from peft import PeftModel


def auto_cls(base):
    """Bira pravu Auto klasu iz configa (Tacit/Qwen=causal, Mistral3=vision-text)."""
    cfg = AutoConfig.from_pretrained(base)
    if type(cfg) in MODEL_FOR_CAUSAL_LM_MAPPING:
        return AutoModelForCausalLM
    assert type(cfg) in MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING, type(cfg)
    return AutoModelForImageTextToText


def load_merged(base, adapter, outdir, dtype=torch.float16):
    if not os.path.exists(os.path.join(outdir, "config.json")):
        print("MERGE-START", base, flush=True)
        tok = AutoTokenizer.from_pretrained(base)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        b = auto_cls(base).from_pretrained(
            base, torch_dtype=dtype, low_cpu_mem_usage=True)
        m = PeftModel.from_pretrained(b, adapter)
        m.merge_and_unload().save_pretrained(outdir)
        tok.save_pretrained(outdir)
        del m, b
        print("MERGED", outdir, flush=True)
    tok = AutoTokenizer.from_pretrained(outdir)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    mdl = auto_cls(outdir).from_pretrained(
        outdir, torch_dtype=dtype, low_cpu_mem_usage=True)
    mdl.eval()
    return tok, mdl


def score_model(model, tok, items, Q, label):
    """Ista metoda kao Tacit readout: chat prompt + A/B/C label-tokeni.
    Jedina razlika: forward ide kroz multimodalnu klasu (Mistral3)."""
    import numpy as np
    from anyjev.question import Question
    from anyjev.readout import build_prompt, render_chat, resolve_labels
    from anyjev.tacit import restricted_logprobs
    recs = []
    for hid, state, opts, exp, lang in items:
        opt_texts = [t for _, t in opts]
        try:
            q = Question.choice(Q.get(lang, Q["bs"]), opt_texts)
            labels, ids = resolve_labels(tok, q)
            perm = list(range(len(opt_texts)))
            spec = build_prompt(state, q, perm, labels=labels)
            text = render_chat(tok, spec)
            enc = tok(text, return_tensors="pt", add_special_tokens=False)
            with torch.no_grad():
                try:
                    logits = model(**enc, logits_to_keep=1).logits[:, -1, :].float()
                except TypeError:
                    logits = model(**enc).logits[:, -1, :].float()
            row = logits[0].cpu().numpy()
            lps = restricted_logprobs([row[i] for i in ids])
            pj = np.exp(np.asarray(lps, dtype=np.float64))
            probs = {opts[perm[j]][1]: float(pj[j]) for j in range(len(opts))}
            best_j = int(np.argmax(lps))
            got = opts[perm[best_j]][0]
            recs.append({"model": label, "id": hid, "expected": exp, "answer_id": got,
                         "probs": {str(k): float(v) for k, v in probs.items()},
                         "correct": (str(got) == str(exp)) if (exp and got) else None})
        except Exception as e:  # noqa: BLE001
            recs.append({"model": label, "id": hid, "error": str(e)[:200]})
        print(json.dumps({"model": label, "id": hid,
                          "correct": recs[-1].get("correct")}), flush=True)
    return recs


OUTD = os.environ.get("READOUT_OUTD", "/home/sha/BH-Decision/datasets/selfdistill")


def load_items():
    held = [json.loads(l) for l in open(
        os.path.join(os.environ.get("READOUT_DATA", "/home/sha/BH-Decision/datasets"),
                     "heldout/heldout-v1.jsonl")) if l.strip()]
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
        BASE = os.environ.get("READOUT_BASE", "mistralai/Ministral-3-8B-Base-2512")
        for label, mid in [("stock-8b", None), ("bh2-9b", os.environ.get("READOUT_ADAPTER", "/tmp/opencode/adapter-9b"))]:
            if mid is None:
                tok = AutoTokenizer.from_pretrained(BASE)
                mdl = auto_cls(BASE).from_pretrained(
                    BASE, torch_dtype=torch.float16, low_cpu_mem_usage=True)
                mdl.eval()
            else:
                tok, mdl = load_merged(BASE, mid, os.environ.get("READOUT_MERGED", "/tmp/opencode/merged-9b"))
            allrecs += score_model(mdl, tok, items, Q, label)
            del mdl
        out = os.path.join(OUTD, "readout-v9b.jsonl")
    else:  # validacija na vA s HF-a
        from huggingface_hub import snapshot_download
        ad = snapshot_download("BH-Language-AI/bh-decision-2-4b",
                               allow_patterns=["adapter_*"])
        tok, mdl = load_merged("morriszjm/Tacit-4B", ad, os.environ.get("READOUT_MERGED_VA", "/tmp/opencode/merged-vA2"))
        allrecs = score_model(mdl, tok, items, Q, "bh2-vA-check")
        del mdl
        out = os.path.join(OUTD, "readout-vA-check.jsonl")
    with open(out, "w") as f:
        for r in allrecs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    for m in sorted(set(r["model"] for r in allrecs)):
        rs = [r for r in allrecs if r["model"] == m and r.get("correct") is not None]
        print(m, sum(1 for r in rs if r["correct"]), "/", len(rs),
              dict(Counter(r.get("answer_id") for r in rs)), flush=True)
    print("GOTOVO", out, flush=True)
