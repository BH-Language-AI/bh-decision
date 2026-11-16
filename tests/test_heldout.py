"""Validacija datasets/heldout/*.jsonl: dvojezičnost je obavezna (bs + en)."""
import glob
import json
import os

import pytest

HELDOUT = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        "datasets", "heldout", "*.jsonl")))


def load_lines(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


@pytest.mark.parametrize("path", HELDOUT or ["<nema heldouta — preskače se>"])
def test_heldout_bilingual_and_sized(path):
    if not HELDOUT:
        pytest.skip("nema datasets/heldout/*.jsonl")
    rs = load_lines(path)
    assert len(rs) >= 10, f"{path}: held-out mora imati bar 10 stavki"
    langs = {r.get("lang") for r in rs}
    assert {"bs", "en"} <= langs, f"{path}: held-out mora sadržavati i bs i en, ima {sorted(langs)}"
