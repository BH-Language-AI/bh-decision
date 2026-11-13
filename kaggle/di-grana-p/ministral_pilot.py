"""BH-Decision Grana P — pilot: Ministral-3-3B-Instruct + LoRA na expanded 400.

EU baza (Mistral AI, Apache-2.0, 3.8B), ijekavica, isti recept kao pilot B
(LoRA r16, fp16, 3 epohe, 90/10 split, format-validity proba).
Model i podaci skidaju se s HF/GitHuba (javno, bez tokena).
Izlaz: /kaggle/working/output (adapter + metrike) + VAL u logu.
"""
import glob
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

COMMIT = "3437ac2"
RAW = f"https://raw.githubusercontent.com/BH-Language-AI/bh-decision/{COMMIT}"
# Ministral-3 je multimodalna arhitektura (vision tower), ali bf16 Base treniramo
# čistim tekstom kroz ImageTextToText klasu — vision tower se ne koristi.
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


cats = ["abstention", "benchmark", "choice", "confidence", "multicriteria",
        "ranking", "risk", "scoring"]
for c in cats:
    fetch(f"{RAW}/datasets/expanded/{c}.jsonl", f"/tmp/bh-data/{c}.jsonl")
fetch(f"{RAW}/kaggle/pilot-b/vendor/harness.py", "/tmp/bh-data/harness.py")
fetch(f"{RAW}/datasets/samples/benchmark.jsonl", "/tmp/bh-data/probe.jsonl")

sh("pip install -q peft datasets 2>&1 | tail -1")
# Kaggle image ima prestar transformers (nema Mistral3 klase) — upgrade s interneta.
sh("pip install -q -U transformers tokenizers 2>&1 | tail -1")
# transformers 5 traži torchao>0.16 (image ima 0.10).
sh("pip install -q -U torchao 2>&1 | tail -1")
# T4 14.5GB ne drži 3.8B fp16 + gradijente → QLoRA nf4 (~2.5GB baza).
sh("pip install -q bitsandbytes 2>&1 | tail -1")

import torch  # noqa: E402
print("cuda:", torch.cuda.is_available(), torch.cuda.get_device_name(0), flush=True)
assert torch.cuda.is_available(), "nema GPU-a, prekidam"

from transformers import (AutoModelForImageTextToText, AutoTokenizer,  # noqa: E402
                          Trainer, TrainingArguments, DataCollatorForLanguageModeling)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training  # noqa: E402
from transformers import BitsAndBytesConfig  # noqa: E402

try:
    tok = AutoTokenizer.from_pretrained(MODEL)
except Exception as e:
    print("MODEL-NEDOSTUPAN (gated?):", str(e)[:200], flush=True)
    raise SystemExit("prekid: model se ne može skinuti bez autorizacije")

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
    if put.endswith("probe.jsonl") or put.endswith("harness.py"):
        continue
    for red in open(put, encoding="utf-8"):
        red = red.strip()
        if not red:
            continue
        r = json.loads(red)
        tekstovi.append({"text": r.get("state", "") + "\nODLUKA: "
                         + json.dumps(r.get("reference", {}), ensure_ascii=False)})
print("redova:", len(tekstovi), flush=True)
assert len(tekstovi) >= 380, "očekivano ~400 primjera"

from datasets import Dataset  # noqa: E402
full = Dataset.from_list(tekstovi)
split = full.train_test_split(test_size=0.1, seed=42)
ds, ds_val = split["train"], split["test"]
print("train/val:", len(ds), len(ds_val), flush=True)


def tok_fn(r):
    return tok(r["text"], truncation=True, max_length=512)


ds = ds.map(tok_fn)
ds_val = ds_val.map(tok_fn)
# T4 14.5GB: batch 1 + kratke sekvence (tekstovi su ~100 tokena) + checkpointing.
args = TrainingArguments(output_dir=f"{OUT}/ckpt-p", per_device_train_batch_size=1,
                         gradient_accumulation_steps=32, learning_rate=2e-4,
                         num_train_epochs=3, fp16=True, gradient_checkpointing=True,
                         logging_steps=10, eval_strategy="epoch", save_strategy="epoch",
                         save_total_limit=1, load_best_model_at_end=True,
                         seed=42, report_to="none")
trainer = Trainer(model=model, args=args, train_dataset=ds, eval_dataset=ds_val,
                  data_collator=DataCollatorForLanguageModeling(tok, mlm=False))
trainer.train()
model.save_pretrained(f"{OUT}/adapter-p")
val = trainer.evaluate()
print("VAL:", val, flush=True)

model.eval()
probe = [json.loads(l) for l in open("/tmp/bh-data/probe.jsonl") if l.strip()]
gen, ok = [], 0
need = {"decision", "confidence"}
for r in probe:
    prompt = r["state"] + "\nODLUKA:"
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        out = model.generate(**{k: v[:, -512:] for k, v in ids.items()},
                             max_new_tokens=256, do_sample=False,
                             pad_token_id=tok.pad_token_id)
    txt = tok.decode(out[0], skip_special_tokens=True)
    frag = txt[len(prompt):].strip()[:800]
    try:
        d = json.loads(frag[frag.index("{"):frag.rindex("}") + 1])
        if need <= set(d):
            ok += 1
    except Exception:  # noqa: BLE001
        pass
    gen.append({"id": r["id"], "generacija": frag})
json.dump(gen, open(f"{OUT}/generacije-p.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
met = {"base": MODEL, "val_loss": val.get("eval_loss"),
       "format_valid_rate": ok / max(1, len(probe)), "n_probe": len(probe),
       "n_train": len(ds), "n_val": len(ds_val)}
json.dump(met, open(f"{OUT}/metrike-p.json", "w", encoding="utf-8"), indent=1)
print("METRIKE:", met, flush=True)
print("GOTOVO: adapter + generacije + metrike u", OUT, flush=True)
