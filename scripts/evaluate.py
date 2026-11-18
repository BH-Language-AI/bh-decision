"""BH-Decision evaluacija — CLI omotač.

Ako postoji benchmarks/harness.py, delegira njemu; inače minimalni scoring:
upoređuje polje 'decision' iz ref i pred (JSON ili JSONL) i ispisuje tačnost.
"""
import argparse
import json
import os
import sys

HARNESS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "benchmarks", "harness.py")


def load_records(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def minimal_score(ref_records, pred_records):
    preds = {r.get("id"): r for r in pred_records if isinstance(r, dict) and "id" in r}
    total, hit = 0, 0
    brier_sum, brier_n = 0.0, 0
    for r in ref_records:
        if not isinstance(r, dict) or "id" not in r:
            continue
        total += 1
        p = preds.get(r["id"], {})
        exp = r.get("decision", r.get("reference"))
        if isinstance(exp, dict):
            exp = exp.get("decision")
        if p.get("decision") == exp:
            hit += 1
        probs = p.get("probs")
        if isinstance(probs, dict) and exp in probs:
            try:
                brier_sum += (1.0 - float(probs[exp])) ** 2
                brier_n += 1
            except (TypeError, ValueError):
                pass
    result = {"total": total, "hit": hit, "accuracy": (hit / total) if total else 0.0}
    if brier_n:  # proper scoring (d1.2 praksa): kaznjava samouvjerene greške
        result["brier"] = round(brier_sum / brier_n, 4)
        result["brier_n"] = brier_n
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="BH-Decision evaluacija.")
    ap.add_argument("--ref", required=True, help="referentni JSON/JSONL")
    ap.add_argument("--pred", required=True, help="predikcije JSON/JSONL")
    ap.add_argument("--out", default=None, help="opciona putanja za JSON rezultat")
    args = ap.parse_args(argv)

    if os.path.exists(HARNESS):
        import runpy
        sys.argv = ["harness.py", "--ref", args.ref, "--pred", args.pred] + \
                   (["--out", args.out] if args.out else [])
        runpy.run_path(HARNESS, run_name="__main__")
        return 0

    result = minimal_score(load_records(args.ref), load_records(args.pred))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
