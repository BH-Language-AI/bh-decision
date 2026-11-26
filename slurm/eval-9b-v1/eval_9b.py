#!/usr/bin/env python3
"""9B eval: stock baza vs baza+adapter, ISTI prompt i ISTA metrika kao in-train proba.
Fair gate za objavu: adapter se objavljuje samo ako je iznad stocka.
Ulaz: --model bazni HF id, --adapter putanja ili prazno za stock, --heldout jsonl, --out dir.
"""
import argparse
import json
import os

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--adapter", default="")
ap.add_argument("--heldout", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoModelForImageTextToText, AutoTokenizer  # noqa: E402

tok = AutoTokenizer.from_pretrained(a.model)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
try:
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.bfloat16)
except ValueError:
    model = AutoModelForImageTextToText.from_pretrained(a.model, torch_dtype=torch.bfloat16)
if a.adapter:
    from peft import PeftModel  # noqa: E402
    model = PeftModel.from_pretrained(model, a.adapter)
    tag = "adapter"
else:
    tag = "stock"
if os.path.exists(f"{a.out}/metrike-{tag}.json"):
    print(f"SKIP: metrike-{tag}.json vec postoje", flush=True)
    raise SystemExit(0)
model.eval()
print(f"eval: {tag} ({a.model})", flush=True)

held = [json.loads(l) for l in open(a.heldout, encoding="utf-8") if l.strip()]
gen, ok, tocno, scored = [], 0, 0, 0
need = {"decision", "confidence"}
for r in held:
    prompt = r["state"] + "\nODLUKA:"
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        out = model.generate(**{k: v[:, -512:] for k, v in ids.items()},
                              max_new_tokens=256, do_sample=False,
                              pad_token_id=tok.pad_token_id)
    txt = tok.decode(out[0], skip_special_tokens=True)
    frag = txt[len(prompt):].strip()[:800]
    rec = {"id": r["id"]}
    try:
        d = json.loads(frag[frag.index("{"):frag.rindex("}") + 1])
        if need <= set(d):
            ok += 1
        rec["generacija"] = d
        if r.get("reference") is not None and d.get("decision") is not None:
            exp = r["reference"].get("decision")
            got = d.get("decision")
            if isinstance(exp, bool):
                got = got is True or (isinstance(got, str) and got.lower() in ("yes", "true"))
            scored += 1
            rec["correct"] = (str(got) == str(exp))
            tocno += rec["correct"]
    except Exception:  # noqa: BLE001
        rec["generacija"] = frag
    gen.append(rec)

json.dump(gen, open(f"{a.out}/heldout-generacije-{tag}.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
met = {"tag": tag, "model": a.model, "format_valid_rate": ok / max(1, len(held)),
       "heldout_accuracy": (tocno / scored) if scored else None,
       "heldout_scored": scored, "n": len(held)}
json.dump(met, open(f"{a.out}/metrike-{tag}.json", "w", encoding="utf-8"), indent=1)
print(f"METRIKE-{tag}:", met, flush=True)
print("EVAL_DONE")
