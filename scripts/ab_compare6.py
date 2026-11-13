#!/usr/bin/env python3
# A/B poredjenje v6 — Muse Spark vs Muse Spark + Jev-1.13-Free.
# OVAJ FAJL: Jev grana (treba OPENCODE_API_KEY; kljuc je mrtav — ceka novi).
# Muse grana: agent odgovara direktno (ab6-muse-20261113.json, rucno, uz napomenu
# da eksperimentator poznaje reference — gornja granica, ne slijepa mjera).
# Istih 16 zadataka obje grane.
import json
import sys

sys.path.insert(0, "scripts")
import ab_compare3 as ab3

IDS = ["d-rmvar", "d-obrisi", "b-rmfile", "b-quote",
       "k-intent-en", "k-tool-bs", "k-route-bs", "k-risk-en",
       "i-rm", "i-readme", "n-skip-risky", "n-skip-benign",
       "c-1a", "c-1b", "e-esc-bs", "e-abs-bs"]


def main():
    import os
    out = sys.argv[1] if len(sys.argv) > 1 else "benchmarks/reports/ab6-20261113.json"
    key = os.environ.get("OPENCODE_API_KEY", "")
    if not key:
        sys.exit("OPENCODE_API_KEY missing (kljuc je mrtav — treba novi)")
    TASKS = []
    seen = set()
    import ab_compare5 as ab5
    for t in list(ab3.TASKS) + list(ab5.TASKS):
        if t["id"] in IDS and t["id"] not in seen:
            seen.add(t["id"])
            TASKS.append(t)
    assert len(TASKS) == len(IDS), f"fali zadataka: {set(IDS) - seen}"
    rows = []
    for t in TASKS:
        r = ab3.ask(t, key)
        rows.append({"id": t["id"], "batch": t["batch"], "arm": "Muse+Jev", "ref": t["ref"], **r,
                     "provider_calls": 1})
    scored = [r for r in rows if r.get("ref") is not None and r.get("correct") is not None]
    tot_ms = sum(r["ms"] for r in rows)
    tot_b = sum(r["bytes"] for r in rows)
    summary = {"arm": "Muse+Jev", "n": len(rows),
               "correct": sum(1 for r in scored if r["correct"]), "scored": len(scored),
               "accuracy": round(sum(1 for r in scored if r["correct"]) / len(scored), 3),
               "provider_calls": sum(r["provider_calls"] for r in rows),
               "total_ms": tot_ms, "avg_ms": round(tot_ms / len(rows), 1),
               "total_bytes": tot_b, "est_tokens": tot_b // 4}
    json.dump({"summary": summary, "results": rows}, open(out, "w"), ensure_ascii=False, indent=1)
    print("SUMMARY " + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
