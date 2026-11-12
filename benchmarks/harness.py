#!/usr/bin/env python3
"""BH-Decision benchmark harness (samo stdlib).

Upotreba: python3 harness.py --ref <ref.jsonl> --pred <pred.jsonl>
Ref red: {id, lang, ..., reference: {...protokol v1.0...}}.
Pred red: {id, prediction: {...protokol v1.0...}}.
Self-test: python3 harness.py --self-test
"""

import argparse
import json
import math
import sys


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def accuracy(rows):
    ok = sum(1 for r, p in rows if r.get("decision") == p.get("decision"))
    return ok / len(rows) if rows else 0.0


def mae_scores(rows):
    errs, n = 0.0, 0
    for r, p in rows:
        rs, ps = r.get("scores") or {}, p.get("scores") or {}
        for k, v in rs.items():
            if k in ps:
                errs += abs(float(v) - float(ps[k]))
                n += 1
    return errs / n if n else None


def brier(rows):
    tot = 0.0
    for r, p in rows:
        correct = 1.0 if r.get("decision") == p.get("decision") else 0.0
        tot += (float(p.get("confidence", 0.0)) - correct) ** 2
    return tot / len(rows) if rows else 0.0


def ece(rows, n_bins=10):
    bins = [[0.0, 0] for _ in range(n_bins)]
    for r, p in rows:
        c = float(p.get("confidence", 0.0))
        b = min(int(c * n_bins), n_bins - 1)
        bins[b][0] += 1.0 if r.get("decision") == p.get("decision") else 0.0
        bins[b][1] += 1
    n = len(rows)
    e = 0.0
    for i, (ok, cnt) in enumerate(bins):
        if cnt:
            e += (cnt / n) * abs(ok / cnt - (i + 0.5) / n_bins)
    return e


def ndcg_mrr(rows, k=5):
    ndcgs, mrrs = [], []
    for r, p in rows:
        ideal = r.get("options_ranked") or []
        pred = p.get("options_ranked") or []
        if not ideal or not pred:
            continue
        rel = {oid: len(ideal) - i for i, oid in enumerate(ideal)}
        kk = min(k, len(ideal))
        dcg = sum(rel.get(oid, 0) / math.log2(i + 2) for i, oid in enumerate(pred[:kk]))
        idcg = sum(sorted(rel.values(), reverse=True)[:kk][i] / math.log2(i + 2) for i in range(kk))
        ndcgs.append(dcg / idcg if idcg else 0.0)
        top = ideal[0]
        mrrs.append(1.0 / (pred.index(top) + 1) if top in pred else 0.0)
    avg = lambda xs: sum(xs) / len(xs) if xs else None
    return avg(ndcgs), avg(mrrs)


def abstention_pr(rows):
    tp = fp = fn = 0
    for r, p in rows:
        rt, pt = r.get("decision") == "abstain", p.get("decision") == "abstain"
        tp += rt and pt
        fp += (not rt) and pt
        fn += rt and (not pt)
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    return prec, rec


def report_for(pairs):
    refs = [r for r, _ in pairs]
    preds = [p for _, p in pairs]
    rp = list(zip(refs, preds))
    prec, rec = abstention_pr(rp)
    ndcg, mrr = ndcg_mrr(rp)
    return {
        "n": len(rp),
        "accuracy": round(accuracy(rp), 4),
        "mae_scores": round(mae_scores(rp), 4) if mae_scores(rp) is not None else None,
        "brier": round(brier(rp), 4),
        "ece_10": round(ece(rp), 4),
        "ndcg@5": round(ndcg, 4) if ndcg is not None else None,
        "mrr": round(mrr, 4) if mrr is not None else None,
        "abstention_precision": round(prec, 4) if prec is not None else None,
        "abstention_recall": round(rec, 4) if rec is not None else None,
    }


def evaluate(ref_rows, pred_rows):
    preds = {p["id"]: p.get("prediction", {}) for p in pred_rows}
    pairs = [(r.get("reference", {}), preds[r["id"]]) for r in ref_rows if r.get("id") in preds]
    missing = [r["id"] for r in ref_rows if r.get("id") not in preds]
    langs = sorted({r.get("lang", "?") for r in ref_rows})
    # lang uzmi iz ref reda (spareno s parom)
    by_lang = {}
    id2lang = {r["id"]: r.get("lang", "?") for r in ref_rows}
    for r, p in pairs:
        # nađi id preko reference — nosi lang iz ref reda
        pass
    out = {"overall": report_for(pairs), "by_lang": {}, "missing_ids": missing}
    for lg in langs:
        lg_pairs = [(r.get("reference", {}), preds[r["id"]]) for r in ref_rows
                    if r.get("id") in preds and r.get("lang") == lg]
        out["by_lang"][lg] = report_for(lg_pairs)
    return out


def self_test():
    ref = [
        {"id": "t1", "lang": "bs", "reference": {"decision": "o1", "options_ranked": ["o1", "o2"],
         "scores": {"o1": 0.9, "o2": 0.2}, "confidence": 0.9}},
        {"id": "t2", "lang": "bs", "reference": {"decision": "abstain", "options_ranked": [],
         "scores": {}, "confidence": 0.3}},
        {"id": "t3", "lang": "en", "reference": {"decision": "o2", "options_ranked": ["o2", "o1"],
         "scores": {"o1": 0.4, "o2": 0.8}, "confidence": 0.8}},
    ]
    pred_ok = [{"id": r["id"], "prediction": dict(r["reference"])} for r in ref]
    out = evaluate(ref, pred_ok)
    assert out["overall"]["accuracy"] == 1.0, out
    assert out["overall"]["mae_scores"] == 0.0, out
    assert out["overall"]["brier"] == round(((0.9 - 1) ** 2 + (0.3 - 1) ** 2 + (0.8 - 1) ** 2) / 3, 4), out
    assert out["overall"]["abstention_precision"] == 1.0, out
    assert out["overall"]["abstention_recall"] == 1.0, out
    assert out["overall"]["mrr"] == 1.0 and out["overall"]["ndcg@5"] == 1.0, out
    bad = [dict(p) for p in pred_ok]
    bad[0] = {"id": "t1", "prediction": dict(ref[0]["reference"], decision="o2")}
    out2 = evaluate(ref, bad)
    assert out2["overall"]["accuracy"] == round(2 / 3, 4), out2
    assert out2["overall"]["abstention_precision"] == 1.0, out2
    assert set(out["by_lang"]) == {"bs", "en"}, out
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=None)
    ap.add_argument("--pred", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    if not a.ref or not a.pred:
        sys.exit("potrebno: --ref <ref.jsonl> --pred <pred.jsonl> (ili --self-test)")
    print(json.dumps(evaluate(load_jsonl(a.ref), load_jsonl(a.pred)),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
