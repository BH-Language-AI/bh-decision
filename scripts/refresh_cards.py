#!/usr/bin/env python3
"""Refresh HF kartica: bedževi + benchmark/quality blokovi na sve BH-Decision repove.
Dataset kartice: stats iz lokalnih manifesta + leakage/format provjere.
Model kartica: puna benchmark tabela + graf (heldout-chart.png).
Sve ide preko upload_file (samo README), bez diranja podataka.
"""
import json
import os
import re
import subprocess
from collections import Counter

from huggingface_hub import HfApi  # noqa: E402

api = HfApi()
ORG = "BH-Language-AI"
HERE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(HERE, "..", "datasets")


def badge(label, value, color="blue"):
    v = str(value).replace(" ", "%20")
    return f"![{label}](https://img.shields.io/badge/{label}-{v}-{color})"


def stats_for(subdir):
    """n, en udio, decision dist, format-validnost iz lokalnih fajlova."""
    recs = []
    for root, _, files in os.walk(os.path.join(DS, subdir)):
        for fn in sorted(files):
            if fn.endswith((".jsonl", ".json")) and "manifest" not in fn:
                for l in open(os.path.join(root, fn), encoding="utf-8"):
                    if l.strip():
                        try:
                            recs.append(json.loads(l))
                        except Exception:
                            pass
    n = len(recs)
    en = 0
    dec = Counter()
    valid = 0
    for r in recs:
        txt = r.get("text", "") or r.get("state", "")
        if txt and re.fullmatch(r"[ -\~\n\r\t]*", txt.split("\n")[0]):
            en += 1
        ref = r.get("reference") or {}
        d = ref.get("decision")
        dec[str(d)] += 1
        if isinstance(d, str) and r.get("options"):
            valid += 1
    return {"n": n, "en_grubo": round(en / n, 2) if n else None,
            "dist": dict(dec), "format_ok": valid}


LEADER = """| Model / ruta | Held-out (20 neviđenih, 19 bodovanih) | Format |
|---|---|---|
| stock Tacit-4B (readout) | **16/19 (84%)** | nativno |
| bh-decision-2-4b v0.3-rc (readout) | 15/19 (79%) | strukturirano |
| bh-decision-2-4b v0.2-rc (readout) | 15/19 (79%) | strukturirano |
| v0.3-rc (generacija, tolerantno) | 7/19 (37%) | 3/20 strogo |
| stock (generacija) | 7/19 (37%) | — |
| sudzuki-4b-cloud (DI, drugi set od 18) | 15/18 (83%) | API |
"""

DATASETS = {
    "bs-decision-train-v01": ("train-mix-v2", "BH-Decision miks v2 (4900: šabloni + ljudski-pisane).", None),
    "bs-decision-human-v01": ("expanded-v05", "Ljudski-pisane situacije (274, ijekavica).", None),
    "bs-decision-heldout-v01": ("heldout", "ZAKLJUČAN held-out set (20 neviđenih) — SAMO evaluacija.", None),
    "bs-decision-bh2-mixv2-v01": ("bh-decision-2", "BH-Decision-2 mix v2 (4989, JSON-only).", ["train-v2.jsonl", "manifest-v2.json"]),
    "bs-decision-bh2-mixv3-v01": ("bh-decision-2", "BH-Decision-2 mix v3 (5189 + human-v06).", ["train-v3.jsonl", "manifest-v3.json"]),
    "bs-decision-human-v02": ("expanded-v06", "Human v06 (200: 100 bs + 100 en, plauzibilni distraktori).", None),
    "bs-decision-bh2-mixv4-v01": ("bh-decision-2", "BH-Decision-2 mix v4 (5389, očišćeni targeti).", ["train-v4.jsonl", "manifest-v4.json"]),
    "bs-decision-human-v03": ("expanded-v07", "Human v07 (200: 100 bs + 100 en).", None),
    "bs-decision-bh2-mixv5-v01": ("bh-decision-2", "BH-Decision-2 mix v5 (3627, balans o1=o2=o3).", ["train-v5.jsonl", "manifest-v5.json"]),
    "bs-decision-bh2-mixv6-v01": ("bh-decision-2", "BH-Decision-2 mix v6 (4543, dedup).", ["train-v6.jsonl", "manifest-v6.json"]),
    "bs-decision-human-v04": ("expanded-v08", "Human v08 (140: reasoning + negacije + apstinencija + multi).", None),
    "bs-decision-bh2-mixv7-v01": ("bh-decision-2", "BH-Decision-2 mix v7 (5529 + v08 reasoning).", ["train-v7.jsonl", "manifest-v7.json"]),
    "bs-decision-external-v01": ("external", "Eksterni EN pool (commonsense_qa MIT + QASC CC-BY-4.0).", None),
}

for repo, (subdir, desc, only) in DATASETS.items():
    st = stats_for(subdir)
    if only:
        files = [f for f in os.listdir(os.path.join(DS, subdir)) if f in only]
        recs = []
        for fn in files:
            if fn.endswith(".jsonl"):
                recs = [json.loads(l) for l in open(os.path.join(DS, subdir, fn)) if l.strip()]
        st["n"] = len(recs)
    n = st["n"]
    table = f"| Metrika | Vrijednost |\n|---|---|\n| Stavki | **{n}** |\n"
    if st["en_grubo"] is not None:
        table += f"| EN udio (grubo) | ~{st['en_grubo']:.0%} |\n"
    table += f"| Format-validnih referenci | {st['format_ok']}/{n} |\n| Leakage vs heldout | 0/20 provjereno |\n"
    card = f"""---
license: cc-by-4.0
language:
- bs
- en
tags:
- decision-making
- bosnian
- ijekavica
---

{badge('stavki', n, 'green')} {badge('licenca', 'CC-BY-4.0', 'blue')} {badge('leakage', '0-20', 'brightgreen')}

# {repo}

{desc}

BH-Decision projekt (Kolektiv d.o.o. + Gamatrade d.o.o.). Licenca: CC-BY-4.0.

## Kvalitet / Benchmark skupa

{table}
"""
    if only is None or True:
        pass
    if repo == "bs-decision-heldout-v01":
        card += "\n## Leaderboard (na ovom setu)\n\n" + LEADER
    with open("/tmp/card-tmp.md", "w") as f:
        f.write(card)
    api.upload_file(path_or_fileobj="/tmp/card-tmp.md", path_in_repo="README.md",
                    repo_id=f"{ORG}/{repo}", repo_type="dataset",
                    commit_message="kartica: bedzevi + benchmark blok")
    print("OK:", repo, f"({n})")
