#!/usr/bin/env python3
"""Upload BH-Decision trening datasetova na Hugging Face (BH-Language-AI org).
Repoi: bs-decision-train-v01, bs-decision-human-v01, bs-decision-heldout-v01.
Svaki dobija README karticu (bs+en), licenca CC-BY-4.0.
"""
import os
import tempfile

from huggingface_hub import HfApi  # noqa: E402

ORG = "BH-Language-AI"
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets")

CARD = """---
license: cc-by-4.0
language:
- bs
- en
tags:
- decision-making
- bosnian
- ijekavica
---

# {title}

{desc_bs}

BH-Decision projekt (Kolektiv d.o.o. + Gamatrade d.o.o.) — skup za treniranje/evaluaciju
modela odlučivanja na bosanskoj ijekavici i engleskom. Licenca: CC-BY-4.0.

{desc_en}

# {title_en}

BH-Decision project — decision-model training/evaluation set in Bosnian (ijekavica) and
English. License: CC-BY-4.0.
"""

JOBS = [
    ("bs-decision-train-v01", "train-mix-v2",
     "BH-Decision miks v2 (4900 stavki: šabloni + ljudski-pisane + held-out izdvojen).",
     "BH-Decision mix v2 (4900 items: templates + human-authored; held-out kept separate)."),
    ("bs-decision-human-v01", "expanded-v05",
     "Ljudski-pisane situacije odlučivanja (274 stavke, ijekavica) — najvredniji podskup.",
     "Human-authored decision situations (274 items, ijekavica) — highest-value subset."),
    ("bs-decision-heldout-v01", "heldout",
     "ZAKLJUČAN held-out set (20 neviđenih stavki) — SAMO za evaluaciju, nikad za trening.",
     "LOCKED held-out set (20 unseen items) — evaluation ONLY, never train on it."),
]

api = HfApi()
for repo, subdir, desc_bs, desc_en in JOBS:
    rid = f"{ORG}/{repo}"
    api.create_repo(repo_id=rid, repo_type="dataset", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(BASE, subdir)
        import glob as _g
        import shutil
        files = sorted(_g.glob(os.path.join(src, "*.json*")))
        assert files, f"nema fajlova u {src}"
        for f in files:
            shutil.copy(f, tmp)
        title = repo
        with open(os.path.join(tmp, "README.md"), "w") as fh:
            fh.write(CARD.format(title=title, title_en=title,
                                 desc_en=desc_en, desc_bs=desc_bs))
        api.upload_folder(repo_id=rid, folder_path=tmp, repo_type="dataset")
    print("OK:", rid, f"({len(files)} fajlova)")
