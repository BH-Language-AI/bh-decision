"""Kreiranje HF kolekcije BH-Decision (FAZA 4, idempotentno).

Kolekcija sadrži referentne modele iz FAZE 1 (planirane baze, teacheri,
baselineovi) uz napomenu o ulozi svakog. Vlastiti BH-Decision-2B/4B/9B modeli
dodaju se tek nakon validacije u FAZI 7 — skripta se tada ponovo pokrene.

Usage: python3 scripts/create_hf_collection.py [--dry-run]
"""
import argparse
import sys

NAMESPACE = "BH-Language-AI"
SLUG = f"{NAMESPACE}/bh-decision"
TITLE = "BH-Decision"
DESCRIPTION = (
    "BH-Decision — Bosnian Decision Models (Kolektiv x Gamatrade). "
    "2B/4B/9B u pripremi; zasad samo referentni modeli FAZE 1."
)

# (repo_id, tip, napomena o ulozi)
ITEMS = [
    ("utter-project/EuroLLM-9B", "model", "Planirana baza za BH-Decision-9B (Apache 2.0, potvrđen hr)."),
    ("utter-project/EuroLLM-1.7B", "model", "Planirana baza za BH-Decision-2B (Apache 2.0)."),
    ("BSC-LT/salamandra-7b", "model", "Ablacija za 2B tier (Apache 2.0)."),
    ("TildeAI/TildeOpen-30b", "model", "Jezički učitelj, eksplicitan bs/hr/sr (CC-BY-4.0)."),
    ("StrandsAgents/strands-decider-2B-hobson-v19", "model", "Decision teacher + recept (Apache 2.0)."),
    ("Cloudflare/clef-flash", "model", "Obavezni baseline i decision teacher u pilotu (Apache 2.0)."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from huggingface_hub import HfApi

    api = HfApi()
    me = api.whoami()["name"]
    print(f"login: {me}")

    if args.dry_run:
        print(f"DRY-RUN: kolekcija {SLUG} + {len(ITEMS)} stavki")
        for repo_id, kind, note in ITEMS:
            print(f"  + {kind}:{repo_id} — {note}")
        return 0

    try:
        existing = api.get_collection(SLUG)
        print(f"kolekcija postoji: {existing.title} ({len(existing.items)} stavki)")
        have = {it.item_id for it in (existing.items or [])}
    except Exception:
        existing = api.create_collection(
            TITLE, namespace=NAMESPACE, description=DESCRIPTION
        )
        print(f"kreirana kolekcija: {existing.slug}")
        have = set()

    for repo_id, kind, note in ITEMS:
        if repo_id in have:
            print(f" skip (već u kolekciji): {repo_id}")
            continue
        api.add_collection_item(SLUG, repo_id, kind, note=note)
        print(f"  dodano: {repo_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
