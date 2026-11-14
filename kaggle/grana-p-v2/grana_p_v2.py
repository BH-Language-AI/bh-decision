"""Grana P v2 — Ministral-3-3B-Base + QLoRA na expanded-v2 (2378) + held-out eval.
Ista receptura kao validirani pilot (QLoRA nf4, fp16, 3 epohe, 90/10).
Podaci s GitHuba (pinani commit), model s HF. Izlaz: adapter + metrike.json.
"""
import glob
import json
import os
import subprocess
import sys
import urllib.request

COMMIT = "d459819"
RAW = f"https://raw.githubusercontent.com/BH-Language-AI/bh-decision/{COMMIT}"
MODEL = "mistralai/Ministral-3-3B-Base-2512"
OUT = "/kaggle/working/output"
os.makedirs(OUT, exist_ok=True)
os.makedirs("/tmp/bh-data", exist_ok=True)


def sh(cmd):
    print("+", cmd, flush=True)
    subprocess.run(cmd, shell=True, check=True)


def fetch(url, dst):
    urllib.request.urlretrieve(url, dst)
    print("fetch:", dst, os.path.getsize(dst), flush=True)


DATASETS = {"expanded-v2": ["abstention", "benchmark", "choice", "confidence", "multicriteria",
                             "ranking", "risk", "scoring"],
            "expanded-v04": ["abstention", "benchmark", "choice", "confidence", "multicriteria",
                             "ranking", "risk", "scoring"]}
for ddir, cats in DATASETS.items():
    for c in cats:
        fetch(f"{RAW}/datasets/{ddir}/{c}.jsonl", f"/tmp/bh-data/{ddir}-{c}.jsonl")
fetch(f"{RAW}/datasets/heldout/heldout-v1.jsonl", "/tmp/bh-data/heldout.jsonl")

sh("pip install -q peft datasets bitsandbytes 2>&1 | tail -1")
sh("pip install -q -U transformers tokenizers 2>&1 | tail -1")

import torch  # noqa: E402
print("cuda:", torch.cuda.is_available(), torch.cuda.get_device_name(0), flush=True)
assert torch.cuda.is_available(), "nema GPU-a"

from transformers import (AutoModelForImageTextToText, AutoTokenizer,  # noqa: E402
                          Trainer, TrainingArguments, DataCollatorForLanguageModeling,
                          BitsAndBytesConfig)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training  # noqa: E402

tok = AutoTokenizer.from_pretrained(MODEL)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForImageTextToText.from_pretrained(
    MODEL, quantization_config=BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16))
model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM"))

tekstovi = []
for put in sorted(glob.glob("/tmp/bh-data/*.jsonl")):
    if put.endswith("heldout.jsonl"):
        continue
    for red in open(put, encoding="utf-8"):
        red = red.strip()
        if not red:
            continue
        r = json.loads(red)
        tekstovi.append({"text": r.get("state", "") + "\nODLUKA: "
                         + json.dumps(r.get("reference", {}), ensure_ascii=False)})
print("redova:", len(tekstovi), flush=True)
assert len(tekstovi) >= 2000, "očekivano ~2378 primjera"

from datasets import Dataset  # noqa: E402
full = Dataset.from_list(tekstovi)
split = full.train_test_split(test_size=0.1, seed=42)
ds, ds_val = split["train"], split["test"]
print("train/val:", len(ds), len(ds_val), flush=True)


def tok_fn(r):
    return tok(r["text"], truncation=True, max_length=512)


ds = ds.map(tok_fn)
ds_val = ds_val.map(tok_fn)
args = TrainingArguments(output_dir=f"{OUT}/ckpt", per_device_train_batch_size=1,
                         gradient_accumulation_steps=32, learning_rate=2e-4,
                         num_train_epochs=3, fp16=True, gradient_checkpointing=True,
                         logging_steps=25, eval_strategy="epoch", save_strategy="epoch",
                         save_total_limit=1, load_best_model_at_end=True,
                         seed=42, report_to="none")
trainer = Trainer(model=model, args=args, train_dataset=ds, eval_dataset=ds_val,
                  data_collator=DataCollatorForLanguageModeling(tok, mlm=False))
trainer.train()
model.save_pretrained(f"{OUT}/adapter")
val = trainer.evaluate()
print("VAL:", val, flush=True)

model.eval()
held = [json.loads(l) for l in open("/tmp/bh-data/heldout.jsonl") if l.strip()]
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
            tocno += 1 if rec["correct"] else 0
    except Exception:  # noqa: BLE001
        rec["generacija"] = frag
    gen.append(rec)
    print(json.dumps({"id": rec["id"], "correct": rec.get("correct")}), flush=True)
json.dump(gen, open(f"{OUT}/heldout-generacije.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
met = {"base": MODEL, "data": "expanded-v2", "val_loss": val.get("eval_loss"),
       "format_valid_rate": ok / max(1, len(held)),
       "heldout_accuracy": (tocno / scored) if scored else None,
       "heldout_scored": scored, "n_probe": len(held),
       "n_train": len(ds), "n_val": len(ds_val)}
json.dump(met, open(f"{OUT}/metrike.json", "w", encoding="utf-8"), indent=1)
print("METRIKE:", met, flush=True)
print("GOTOVO:", OUT, flush=True)
