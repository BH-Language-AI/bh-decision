"""Validacija configs/*.yaml — pyyaml ako postoji, inače tolerantno parsiranje redova."""
import os

import pytest

try:
    import yaml  # type: ignore
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = [os.path.join(ROOT, "configs", n) for n in ("2b.yaml", "4b.yaml", "9b.yaml")]
KEYS = ("base_model", "lora", "data_mix")


def load_tolerant(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if HAVE_YAML:
        return yaml.safe_load(text)
    cfg = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or ":" not in s:
            continue
        if line[0] in (" ", "\t"):  # ugniježđeni ključ — preskoči na top-levelu
            continue
        k, v = s.split(":", 1)
        cfg[k.strip()] = v.strip()
    return cfg


@pytest.mark.parametrize("path", CONFIGS)
def test_config_exists_and_has_keys(path):
    assert os.path.exists(path), f"nedostaje {path}"
    cfg = load_tolerant(path)
    assert isinstance(cfg, dict) and cfg, f"{path}: prazan config"
    for key in KEYS:
        assert key in cfg, f"{path}: nedostaje ključ '{key}'"


@pytest.mark.parametrize("path", CONFIGS)
def test_config_mentions_lora_params(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for token in ("r: 16", "alpha: 32", "seed: 42", "bf16", "4096"):
        assert token in text, f"{path}: nedostaje '{token}'"
