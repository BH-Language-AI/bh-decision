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
    ("bs-decision-bh2-mixv2-v01", "bh-decision-2",
     "BH-Decision-2 mix v2 (4989 stavki, samo JSON ciljevi: šabloni + human; bez think-tragova i bosnian-core spama; o2 prior srezan).",
     "BH-Decision-2 mix v2 (4989 items, JSON targets only: templates + human; no think-traces, no bosnian-core spam; o2 prior subsampled).",
     ["train-v2.jsonl", "manifest-v2.json"]),
    ("bs-decision-bh2-mixv3-v01", "bh-decision-2",
     "BH-Decision-2 mix v3 (5189: mix v2 + 200 human-v06 s plauzibilnim distraktorima, balans o1/o2/o3; en 10%).",
     "BH-Decision-2 mix v3 (5189: mix v2 + 200 human-v06 with plausible distractors, balanced o1/o2/o3; en 10%).",
     ["train-v3.jsonl", "manifest-v3.json"]),
    ("bs-decision-human-v02", "expanded-v06",
     "Ljudski-pisane situacije v06 (200 stavki, 100 bs + 100 en, plauzibilni distraktori, balansirane reference).",
     "Human-authored situations v06 (200 items, 100 bs + 100 en, plausible distractors, balanced references)."),
    ("bs-decision-bh2-mixv4-v01", "bh-decision-2",
     "BH-Decision-2 mix v4 (5389: mix v3 + 200 human-v07; targeti očišćeni na 7 ključeva, bez metadata papagaja; en 12%).",
     "BH-Decision-2 mix v4 (5389: mix v3 + 200 human-v07; targets cleaned to 7 keys, no metadata parroting; en 12%).",
     ["train-v4.jsonl", "manifest-v4.json"]),
    ("bs-decision-human-v03", "expanded-v07",
     "Ljudski-pisane situacije v07 (200 stavki, 100 bs + 100 en, plauzibilni distraktori, o1 50/o2 50/o3 100).",
     "Human-authored situations v07 (200 items, 100 bs + 100 en, plausible distractors, o1 50/o2 50/o3 100)."),
    ("bs-decision-bh2-mixv5-v01", "bh-decision-2",
     "BH-Decision-2 mix v5 (3627: mix v4 balansiran o1=o2=o3=778; odlučujući eksperiment protiv prior-defaulta).",
     "BH-Decision-2 mix v5 (3627: mix v4 balanced o1=o2=o3=778; decisive experiment vs prior-defaulting).",
     ["train-v5.jsonl", "manifest-v5.json"]),
    ("bs-decision-bh2-mixv6-v01", "bh-decision-2",
     "BH-Decision-2 mix v6 (4543: mix v4 dedup, prvi ostaje; 5-epoha run, zadnji template eksperiment).",
     "BH-Decision-2 mix v6 (4543: deduped mix v4, first kept; 5-epoch run, last template experiment).",
     ["train-v6.jsonl", "manifest-v6.json"]),
        ("bs-decision-bh2-mixv7-v01", "bh-decision-2",
     "BH-Decision-2 mix v7 (5529: mix v4 + v08 full; reasoning tragovi zadrzavaju rationale_full).",
     "BH-Decision-2 mix v7 (5529: mix v4 + v08 full; reasoning traces keep rationale_full).",
     ["train-v7.jsonl", "manifest-v7.json"]),
    ("bs-decision-external-v02", "external",
     "Eksterni EN ETHICS (35701: commonsense+justice train, yes_no moralni sudovi, MIT).",
     "External EN ETHICS (35701: commonsense+justice train, yes_no moral judgments, MIT).",
     ["ethics-commonsense-train.jsonl", "ethics-justice-train.jsonl", "manifest-external-ethics.json"]),
("bs-decision-external-v01", "external",
     "Eksterni EN pool (17875: commonsense_qa MIT + allenai/qasc CC-BY-4.0, samo train; konvertovano u BH format s atribucijom).",
     "External EN pool (17875: commonsense_qa MIT + allenai/qasc CC-BY-4.0, train only; converted to BH format with attribution)."),
    ("bs-decision-human-v04", "expanded-v08",
     "Human v08 (140: reasoning traces 60 + negacije 30 + apstinencija 20 + multi-choice 30; bs/en 70/70; novi tipovi).",
     "Human v08 (140: reasoning traces 60 + negations 30 + abstention 20 + multi-choice 30; bs/en 70/70; new types)."),
]

api = HfApi()
for job in JOBS:
    repo, subdir, desc_bs, desc_en = job[:4]
    only = job[4] if len(job) > 4 else None
    rid = f"{ORG}/{repo}"
    api.create_repo(repo_id=rid, repo_type="dataset", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(BASE, subdir)
        import glob as _g
        import shutil
        files = sorted(_g.glob(os.path.join(src, "*.json*")))
        if only:
            files = [f for f in files if os.path.basename(f) in only]
        assert files, f"nema fajlova u {src}"
        for f in files:
            shutil.copy(f, tmp)
        title = repo
        with open(os.path.join(tmp, "README.md"), "w") as fh:
            fh.write(CARD.format(title=title, title_en=title,
                                 desc_en=desc_en, desc_bs=desc_bs))
        api.upload_folder(repo_id=rid, folder_path=tmp, repo_type="dataset")
    print("OK:", rid, f"({len(files)} fajlova)")
