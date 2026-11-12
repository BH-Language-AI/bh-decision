"""BH-Decision pilot B — GPU smoke test na Kaggleu (FAZA 5).

Cilj: dokazati da pipeline radi na GPU-u (LoRA SFT + loss pada + ijekavske
generacije), NE finalni kvalitet — seed je samo 40 primjera.
T4-sigurno: fp16 (T4 nema bf16), mali batch, max 100 koraka.
OFFLINE kernel: bez git clonea i bez HF downloada — model dolazi iz
model_sources (/kaggle/input), seed+harness su u vendor/ (kopije iz repoa).
"""
import glob
import json
import os
import pathlib
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = "/kaggle/input/bh-decision-seed-v01"
VENDOR = DATA if os.path.isdir(DATA) else os.path.join(HERE, "vendor")
SEED_GLOB = os.path.join(VENDOR, "samples", "*.jsonl")
HARNESS = os.path.join(VENDOR, "harness.py")
OUT = "/kaggle/working/output"

hits = sorted(pathlib.Path("/kaggle/input").rglob("config.json"))
print("config.json na:", [str(h) for h in hits][:5], flush=True)
BASE = str(hits[0].parent) if hits else None
print("model dir:", BASE, flush=True)
assert BASE, "nema modela u /kaggle/input/eurollm-17b"


def sh(cmd):
    print("+", cmd, flush=True)
    subprocess.run(cmd, shell=True, check=True)


# Kaggle image ima prestar torchao (0.10) koji ruši import pefta; ne treba nam.
sh("pip uninstall -y torchao 2>&1 | tail -1")
# Offline: noviji transformers+tokenizers iz dataseta (Kaggle image ima prestar,
# a sentencepiece nema cp313 wheel i kernel nema internet).
sh("pip install --no-index --find-links /kaggle/input/bh-decision-seed-v01 /kaggle/input/bh-decision-seed-v01/transformers-5.22.2-py3-none-any.whl 2>&1 | tail -3")
sh("python3 -c \"import transformers, tokenizers; print('tf:', transformers.__version__, '| tok:', tokenizers.__version__)\"")
sh(f"python3 {HARNESS} --self-test")

import torch
print("cuda:", torch.cuda.is_available(), torch.cuda.get_device_name(0))
assert torch.cuda.is_available(), "nema GPU-a, prekidam"

from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model

tok = AutoTokenizer.from_pretrained(BASE)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float16)
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM"))

files = sorted(glob.glob(SEED_GLOB))
tekstovi = []
for put in files:
    with open(put, encoding="utf-8") as f:
        for red in f:
            red = red.strip()
            if not red:
                continue
            r = json.loads(red)
            tekstovi.append({"text": r.get("state", "") + "\nODLUKA: "
                             + json.dumps(r.get("reference", {}), ensure_ascii=False)})
print("seed redova:", len(tekstovi), flush=True)
assert tekstovi, "nema seed podataka"
from datasets import Dataset
ds = Dataset.from_list(tekstovi)


def tok_fn(r):
    return tok(r["text"], truncation=True, max_length=1024)


ds = ds.map(tok_fn)
args = TrainingArguments(output_dir=f"{OUT}/ckpt-b", per_device_train_batch_size=2,
                         gradient_accumulation_steps=8, learning_rate=2e-4,
                         max_steps=100, fp16=True, gradient_checkpointing=True,
                         logging_steps=10, save_steps=100, save_total_limit=1,
                         seed=42, report_to="none")
Trainer(model=model, args=args, train_dataset=ds,
        data_collator=DataCollatorForLanguageModeling(tok, mlm=False)).train()
model.save_pretrained(f"{OUT}/adapter-b")

model.eval()
probe = [json.loads(l) for l in open(os.path.join(VENDOR, "samples", "benchmark.jsonl"))][:3]
gen = []
for r in probe:
    prompt = r["state"] + "\nODLUKA:"
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        out = model.generate(**{k: v[:, -512:] for k, v in ids.items()},
                             max_new_tokens=96, do_sample=False, pad_token_id=tok.pad_token_id)
    gen.append({"id": r["id"], "generacija": tok.decode(out[0], skip_special_tokens=True)[-600:]})
json.dump(gen, open(f"{OUT}/generacije-b.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("GOTOVO: adapter + 3 generacije u", OUT, flush=True)
