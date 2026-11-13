#!/usr/bin/env python3
"""Grana P v2 — Ministral-3-3B-Base + LoRA bf16 na LUMI (MI250X, ROCm, bez bitsandbytes).
Trening na expanded-v2 (~2378), evaluacija: val split + held-out v1 (20 neviđenih).
Izlaz: adapter + metrike.json u OUT.
"""
import argparse
import glob
import json
import os

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--model", default="mistralai/Ministral-3-3B-Base-2512")
ap.add_argument("--epochs", type=int, default=3)
a = ap.parse_args()
os.makedirs(f"{a.out}/adapter", exist_ok=True)

import torch  # noqa: E402
assert torch.cuda.is_available(), "nema GPU-a"
print("cuda:", torch.cuda.get_device_name(0), flush=True)

from transformers import (AutoModelForImageTextToText, AutoTokenizer,  # noqa: E402
                          Trainer, TrainingArguments, DataCollatorForLanguageModeling)
from peft import LoraConfig, get_peft_model  # noqa: E402
from torch.utils.data import Dataset as TorchDataset  # noqa: E402 (izbjegava datasets/pyarrow fingerprint bug)

tok = AutoTokenizer.from_pretrained(a.model)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForImageTextToText.from_pretrained(a.model, torch_dtype=torch.bfloat16)
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM"))

tekstovi = []
for put in sorted(glob.glob(os.path.join(a.data, "expanded-v2", "*.jsonl"))):
    for red in open(put, encoding="utf-8"):
        red = red.strip()
        if not red:
            continue
        r = json.loads(red)
        tekstovi.append({"text": r.get("state", "") + "\nODLUKA: "
                         + json.dumps(r.get("reference", {}), ensure_ascii=False)})
print("redova:", len(tekstovi), flush=True)
assert len(tekstovi) >= 2000, "očekivano ~2378 primjera"


class Enc(TorchDataset):
    def __init__(self, rows):
        self.e = [tok(r["text"] if isinstance(r, dict) else r, truncation=True, max_length=512)
                  for r in rows]

    def __len__(self):
        return len(self.e)

    def __getitem__(self, i):
        return {k: torch.tensor(v) for k, v in self.e[i].items()}


idx = list(range(len(tekstovi)))
__import__("random").Random(42).shuffle(idx)
cut = int(len(idx) * 0.9)
ds = Enc([tekstovi[i] for i in idx[:cut]])
ds_val = Enc([tekstovi[i] for i in idx[cut:]])
print("train/val:", len(ds), len(ds_val), flush=True)
args = TrainingArguments(output_dir=f"{a.out}/ckpt", per_device_train_batch_size=2,
                         gradient_accumulation_steps=16, learning_rate=2e-4,
                         num_train_epochs=a.epochs, bf16=True, gradient_checkpointing=True,
                         logging_steps=10, eval_strategy="epoch", save_strategy="epoch",
                         save_total_limit=1, load_best_model_at_end=True,
                         seed=42, report_to="none")
trainer = Trainer(model=model, args=args, train_dataset=ds, eval_dataset=ds_val,
                  data_collator=DataCollatorForLanguageModeling(tok, mlm=False))
trainer.train()
model.save_pretrained(f"{a.out}/adapter")
val = trainer.evaluate()
print("VAL:", val, flush=True)

model.eval()
held = [json.loads(l) for l in open(os.path.join(a.data, "heldout", "heldout-v1.jsonl")) if l.strip()]
gen, ok, tocno, scored = [], 0, 0, 0
need = {"decision", "confidence"}
for r in held:
    prompt = r["state"] + "\nODLUKA:"
    ids = tok(prompt, return_tensors=True).to(model.device)
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
            if str(got) == str(exp):
                tocno += 1
                rec["correct"] = True
            else:
                rec["correct"] = False
    except Exception:  # noqa: BLE001
        rec["generacija"] = frag
    gen.append(rec)
json.dump(gen, open(f"{a.out}/heldout-generacije.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
met = {"base": a.model, "val_loss": val.get("eval_loss"),
       "format_valid_rate": ok / max(1, len(held)),
       "heldout_accuracy": (tocno / scored) if scored else None,
       "heldout_scored": scored, "n_probe": len(held),
       "n_train": len(ds), "n_val": len(ds_val)}
json.dump(met, open(f"{a.out}/metrike.json", "w", encoding="utf-8"), indent=1)
print("METRIKE:", met, flush=True)
print("GOTOVO:", a.out, flush=True)
