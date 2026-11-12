"""BH-Decision pilot FAZE 5 — A vs B vs C (izvršni).

Dry-run (podrazumijevan): validira config kraka, provjerava seed JSONL i
harness, ispisuje plan — bez GPU-a i bez ikakvog downloada modela.
Pravi rad: traži GPU (torch.cuda.is_available), --confirm i
env BH_DECISION_ALLOW_TRAIN=1.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

ARMS = {
    "a": {
        "base_model": "StrandsAgents/strands-decider-2B-hobson-v19",
        "config": "configs/2b.yaml",
        "opis": "LoRA SFT na seed podacima",
        "koraci": 150,
        "vram": "1x24GB",
        "vrijeme": "~1-2h",
    },
    "b": {
        "base_model": "utter-project/EuroLLM-1.7B",
        "config": "configs/2b.yaml",
        "opis": "jezicka adaptacija (bs:en 75/25) + scoring/pointer glava",
        "koraci": 300,
        "vram": "1x24GB",
        "vrijeme": "~2-4h",
    },
    "c": {
        "base_model": "utter-project/EuroLLM-1.7B",
        "config": "configs/2b.yaml",
        "opis": "B + distilacija (clef-flash + TildeOpen-30B ijekavski primjeri)",
        "koraci": 600,
        "vram": "1x24GB",
        "vrijeme": "~4-8h ukljucujuci teacher inferencu",
    },
}

SEED_GLOB = "datasets/samples/*.jsonl"
HARNESS = "benchmarks/harness.py"


def ucitaj_config(path):
    try:
        import yaml  # type: ignore
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        cfg = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                k, v = line.split(":", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
        return cfg


def dry_run(arm):
    spec = ARMS[arm]
    cfg = ucitaj_config(spec["config"])
    for kljuc in ("base_model", "lora", "data_mix", "training", "model"):
        if kljuc not in cfg:
            raise ValueError(f"{spec['config']}: nedostaje kljuc: {kljuc}")
    seed_fajlovi = sorted(glob.glob(SEED_GLOB))
    if not seed_fajlovi:
        raise ValueError(f"nema seed podataka: {SEED_GLOB}")
    ukupno = 0
    for put in seed_fajlovi:
        with open(put, encoding="utf-8") as f:
            for red in f:
                if red.strip():
                    json.loads(red)
                    ukupno += 1
    if ukupno < 40:
        raise ValueError(f"seed ima {ukupno} primjera, ocekuje se >= 40")
    r = subprocess.run([sys.executable, HARNESS, "--self-test"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise ValueError(f"harness self-test pao: {r.stderr.strip()}")
    print(f"krak: {arm} — {spec['opis']}")
    print(f"  model: {spec['base_model']}")
    print(f"  config: {spec['config']}")
    print(f"  seed: {ukupno} primjera u {len(seed_fajlovi)} datoteka")
    print(f"  koraci: ~{spec['koraci']}, VRAM: {spec['vram']}, vrijeme: {spec['vrijeme']}")
    print(f"  eval: {HARNESS} (accuracy, ndcg@5, mrr, mae_scores, brier, ece_10, abstention P/R, by_lang)")
    print("  rezim: DRY-RUN — GPU nije dotaknut, nista nije preuzeto.")
    return 0


def pravi_rad(arm, confirm):
    if not confirm or os.environ.get("BH_DECISION_ALLOW_TRAIN") != "1":
        print("ODBIJENO: pravi trening trazi --confirm i BH_DECISION_ALLOW_TRAIN=1.",
              file=sys.stderr)
        return 2
    import torch  # lazy: samo na putu pravog treninga
    if not torch.cuda.is_available():
        print("ODBIJENO: nema GPU-a (torch.cuda.is_available() je False).", file=sys.stderr)
        return 2
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer  # lazy
    from peft import LoraConfig, get_peft_model  # lazy
    from datasets import load_dataset  # lazy

    spec = ARMS[arm]
    lora_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                          target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                          "gate_proj", "up_proj", "down_proj"],
                          task_type="CAUSAL_LM")
    tok = AutoTokenizer.from_pretrained(spec["base_model"])
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(spec["base_model"], torch_dtype=torch.bfloat16)
    model = get_peft_model(model, lora_cfg)
    ds = load_dataset("json", data_files=sorted(glob.glob(SEED_GLOB)), split="train")

    def tokenizuj(red):
        tekst = red.get("state", "") + " " + json.dumps(red.get("reference", {}),
                                                        ensure_ascii=False)
        return tok(tekst, truncation=True, max_length=4096)

    ds = ds.map(tokenizuj)
    args = TrainingArguments(output_dir=f"checkpoints/pilot-{arm}", per_device_train_batch_size=4,
                             gradient_accumulation_steps=8, learning_rate=2.0e-4,
                             num_train_epochs=3, bf16=True, gradient_checkpointing=True,
                             eval_strategy="no", save_steps=200, save_total_limit=3,
                             seed=42, report_to="none")
    Trainer(model=model, args=args, train_dataset=ds).train()
    model.save_pretrained(f"checkpoints/pilot-{arm}")
    r = subprocess.run([sys.executable, HARNESS, "--ref", "datasets/samples/benchmark.jsonl",
                        "--pred", f"preds/{arm}.jsonl"], capture_output=True, text=True)
    print(r.stdout)
    return r.returncode


def main(argv=None):
    ap = argparse.ArgumentParser(description="BH-Decision pilot FAZE 5 (A vs B vs C).")
    ap.add_argument("--arm", choices=tuple(ARMS), required=True)
    ap.add_argument("--dry-run", dest="dry_run", action=argparse.BooleanOptionalAction,
                    default=True, help="samo validiraj i ispisi plan (podrazumijevano)")
    ap.add_argument("--confirm", action="store_true",
                    help="eksplicitna potvrda za pravi rad na GPU-u")
    args = ap.parse_args(argv)
    if args.dry_run:
        return dry_run(args.arm)
    return pravi_rad(args.arm, args.confirm)


if __name__ == "__main__":
    sys.exit(main())
