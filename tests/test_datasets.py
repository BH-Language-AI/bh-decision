"""Validacija datasets/samples/*.jsonl (stdlib only)."""
import glob
import json
import os

import pytest

SAMPLES = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        "datasets", "samples", "*.jsonl")))

REQUIRED = {"id", "lang", "state", "reference", "source", "license"}
LANGS = {"bs", "en"}


def load_lines(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                pytest.fail(f"{path}:{n}: nevalidan JSON: {e}")
    return records


@pytest.mark.parametrize("path", SAMPLES or ["<nema uzoraka — preskače se>"])
def test_jsonl_valid_and_fields(path):
    if not SAMPLES:
        pytest.skip("nema datasets/samples/*.jsonl")
    for n, r in enumerate(load_lines(path), 1):
        assert isinstance(r, dict), f"{path}:{n}: red mora biti JSON objekt"
        missing = REQUIRED - set(r)
        assert not missing, f"{path}:{n}: nedostaju polja {sorted(missing)}"
        assert r["lang"] in LANGS, f"{path}:{n}: lang mora biti bs|en"


def test_unique_ids_and_bs_ratio():
    if not SAMPLES:
        pytest.skip("nema datasets/samples/*.jsonl")
    ids, bs, total = set(), 0, 0
    for path in SAMPLES:
        for r in load_lines(path):
            total += 1
            assert r["id"] not in ids, f"duplikat id: {r['id']}"
            ids.add(r["id"])
            if r["lang"] == "bs":
                bs += 1
    assert total > 0, "uzorci su prazni"
    assert bs / total >= 0.6, f"barem 60% primjera na bs, dobijeno {bs}/{total}"
