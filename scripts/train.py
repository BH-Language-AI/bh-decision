"""BH-Decision trening stub — FAZA 4 (infrastruktura).

Pravi trening pripada FAZI 5/6 i odbija se bez --confirm i bez
env BH_DECISION_ALLOW_TRAIN=1. Dry-run (podrazumijevan) samo validira
config i ispisuje plan — ne dira GPU.
"""
import argparse
import os
import sys


def load_config(path):
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


def validate_config(cfg, path):
    required = ["base_model", "lora", "data_mix", "training", "model"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"{path}: nedostaju ključevi: {missing}")
    lora = cfg["lora"] if isinstance(cfg.get("lora"), dict) else {}
    if lora and (lora.get("r") != 16 or lora.get("alpha") != 32):
        raise ValueError(f"{path}: LoRA mora biti r=16, alpha=32")
    return True


def print_plan(cfg, path):
    model = cfg.get("model", {}) if isinstance(cfg.get("model"), dict) else {}
    training = cfg.get("training", {}) if isinstance(cfg.get("training"), dict) else {}
    mix = cfg.get("data_mix", {}) if isinstance(cfg.get("data_mix"), dict) else {}
    print(f"Config: {path}")
    print(f"  base_model: {cfg.get('base_model')}")
    print(f"  precision: {model.get('precision', 'bf16')}, max_seq_length: {model.get('max_seq_length', 4096)}")
    print(f"  data_mix bs/en: {mix.get('bs', '?')}/{mix.get('en', '?')}, seed: {training.get('seed', 42)}")
    print(f"  batch: {training.get('per_device_train_batch_size', '?')} x "
          f"{training.get('gradient_accumulation_steps', '?')} akum., lr: {training.get('learning_rate', '?')}")
    print(f"  eval svakih: {training.get('eval_every_steps', '?')} koraka; "
          f"ckpt: {training.get('save_every_steps', '?')} koraka")
    print("  VRAM procjena (gruba, iz FAZE 1): 2B LoRA 1x24GB; 4B LoRA 1x24-48GB; "
          "9B LoRA 1x24-48GB, full 1-2x80GB.")
    print("  Režim: DRY-RUN — GPU nije dotaknut.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="BH-Decision trening stub (FAZA 4).")
    ap.add_argument("--config", required=True, help="putanja do configs/*.yaml")
    ap.add_argument("--dry-run", dest="dry_run", action=argparse.BooleanOptionalAction,
                    default=True, help="samo validiraj i ispiši plan (podrazumijevano uključeno)")
    ap.add_argument("--confirm", action="store_true",
                    help="eksplicitna potvrda za pravi trening (FAZA 5/6)")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    validate_config(cfg, args.config)
    print_plan(cfg, args.config)

    if args.dry_run:
        return 0

    # Pravi trening: FAZA 5/6, dvostruka zaštita.
    if not args.confirm or os.environ.get("BH_DECISION_ALLOW_TRAIN") != "1":
        print("ODBIJENO: pravi trening je FAZA 5/6 — treba --confirm i "
              "BH_DECISION_ALLOW_TRAIN=1.", file=sys.stderr)
        return 2

    import torch  # noqa: F401  (lazy: samo na putu pravog treninga)
    import transformers  # noqa: F401
    import peft  # noqa: F401
    raise NotImplementedError("Pravi trening se implementira u FAZI 5/6.")


if __name__ == "__main__":
    sys.exit(main())
