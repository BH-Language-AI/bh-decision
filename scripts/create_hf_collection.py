"""Kreiranje HF kolekcije BH-Decision (FAZA 4, idempotentno).

Kolekcija sadrži referentne modele iz FAZE 1 (planirane baze, teacheri,
baselineovi) uz napomenu o ulozi svakog. Vlastiti BH-Decision-2B/4B/9B modeli
dodaju se tek nakon validacije u FAZI 7 — skripta se tada ponovo pokrene.

Usage: python3 scripts/create_hf_collection.py [--dry-run]
"""
import argparse
import sys

NAMESPACE = "BH-Language-AI"
SLUG = f"{NAMESPACE}/bh-decision-6af57d53051dc84ba678cb41"  # puni slug; kratki puca na delete
TITLE = "BH-Decision"
DESCRIPTION = (
    "BH-Decision — Bosnian Decision Models (Kolektiv x Gamatrade). "
    "Vlastiti 4B (v0.5-rc, readout 18/19) i 2B (v2b, readout 13/19); "
    "6 vanjskih referenci FAZE 1 uklonjeno 26.11.2026."
)

# (repo_id, tip, napomena o ulozi)
# Vanjske reference (FAZA 1) uklonjene iz kolekcije 26.11.2026 — imamo svoje modele.
# Bile su: EuroLLM-9B/1.7B, salamandra-7b, TildeOpen-30b, strands-decider-2B, clef-flash.
ITEMS = [
    ("BH-Language-AI/bh-decision-2-4b", "model", "Vlastiti 4B: v0.5-rc readout 18/19 (RC)."),
    ("BH-Language-AI/bh-decision-2-2b", "model", "Vlastiti 2B: v2b readout 13/19 (RC)."),
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
