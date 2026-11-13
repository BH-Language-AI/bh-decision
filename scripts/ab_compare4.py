#!/usr/bin/env python3
# A/B poredjenje v4 — najteze i najduze: istih 52 zadataka kao v3, ali model je
# LOKALNI Tacit-4B preko AnyJev bridgea (bez API kljuca; kljuc je mrtav).
# Grana A (model sam): sve direktno jedan /v1/decide poziv.
# Grana B (model + skill): precheck pravilo -> normalizovan kes -> model.
# Odgovori: choice kljuc; yes_no YES/NO/true/false/1/0 normalizirano.
import json
import re
import subprocess
import sys
import time

BASE = "http://127.0.0.1:8101"


def post(item, timeout):
    body = json.dumps(item)
    t0 = time.time()
    p = subprocess.run(["curl", "-sS", "-m", str(timeout), "-X", "POST", BASE + "/v1/decide",
                        "-H", "Content-Type: application/json", "-d", body],
                       capture_output=True, text=True)
    ms = round((time.time() - t0) * 1000)
    if p.returncode != 0:
        return -1, {"error": p.stderr[:200]}, ms, len(body)
    try:
        return 200, json.loads(p.stdout or "{}"), ms, len(body) + len(p.stdout or "")
    except Exception:
        return -1, {"error": (p.stdout or "")[:200]}, ms, len(body)


def ask(task):
    item = {"state": task["state"], "question": task["q"]}
    if task["kind"] == "yesno":
        item["kind"] = "yes_no"
    else:
        item["kind"] = "choice"
        item["options"] = list((task["options"] if task["kind"] == "choice" else
                                {"low": "", "medium": "", "high": ""}).keys())
    st, body, ms, nbytes = post(item, 180)
    if st != 200 or not isinstance(body, dict):
        return {"answer": None, "http": st, "ms": ms, "bytes": nbytes, "correct": None,
                "error": (body.get("error", body) if isinstance(body, dict) else body)}
    a = body.get("answer")
    if task["kind"] == "yesno":
        truthy = str(a).strip().lower() in ("yes", "true", "1", "y")
        falsy = str(a).strip().lower() in ("no", "false", "0", "n")
        if not (truthy or falsy):
            return {"answer": a, "http": st, "ms": ms, "bytes": nbytes, "correct": None, "error": "bad yes_no"}
        return {"answer": a, "http": st, "ms": ms, "bytes": nbytes,
                "correct": (truthy == bool(task["ref"])) if task.get("ref") is not None else None}
    if isinstance(a, str):
        return {"answer": a, "http": st, "ms": ms, "bytes": nbytes,
                "correct": (a == str(task["ref"])) if task.get("ref") is not None else None}
    return {"answer": a, "http": st, "ms": ms, "bytes": nbytes, "correct": None, "error": "bad shape"}


def main():
    sys.path.insert(0, "scripts")
    import ab_compare3 as ab
    out = sys.argv[1] if len(sys.argv) > 1 else "benchmarks/reports/ab4-20261113.json"
    TASKS, PRECHECK = ab.TASKS, ab.PRECHECK
    cache = {}
    rows = []
    for t in TASKS:
        r = ask(t)
        rows.append({"id": t["id"], "batch": t["batch"], "arm": "A-sam", "ref": t["ref"], **r,
                     "provider_calls": 1, "precheck": False, "cache": False})
    for t in TASKS:
        rule = next((rid for rx, rid in PRECHECK if rx.search(t["state"])), None)
        if rule:
            rows.append({"id": t["id"], "batch": t["batch"], "arm": "B-skill", "ref": t["ref"],
                         "answer": "high", "http": 200, "ms": 0, "bytes": 0,
                         "correct": t["ref"] == "high" if t.get("ref") is not None else None,
                         "provider_calls": 0, "precheck": rule, "cache": False})
            continue
        k = ab.normkey(t)
        if k in cache:
            c = dict(cache[k])
            c.update({"id": t["id"], "batch": t["batch"], "arm": "B-skill", "ms": 0, "bytes": 0,
                      "provider_calls": 0, "precheck": False, "cache": True})
            rows.append(c)
            continue
        r = ask(t)
        cache[k] = dict(r, ref=t["ref"])
        rows.append({"id": t["id"], "batch": t["batch"], "arm": "B-skill", "ref": t["ref"], **r,
                     "provider_calls": 1, "precheck": False, "cache": False})

    def agg(arm):
        rs = [r for r in rows if r["arm"] == arm]
        scored = [r for r in rs if r.get("ref") is not None and r.get("correct") is not None]
        tot_ms = sum(r["ms"] for r in rs)
        tot_b = sum(r["bytes"] for r in rs)
        return {"arm": arm, "n": len(rs), "correct": sum(1 for r in scored if r["correct"]),
                "scored": len(scored),
                "accuracy": round(sum(1 for r in scored if r["correct"]) / len(scored), 3) if scored else None,
                "provider_calls": sum(r["provider_calls"] for r in rs),
                "total_ms": tot_ms, "avg_ms": round(tot_ms / len(rs), 1),
                "total_bytes": tot_b, "est_tokens": tot_b // 4,
                "precheck_hits": sum(1 for r in rs if r["precheck"]),
                "cache_hits": sum(1 for r in rs if r["cache"])}

    summary = {"arms": [agg("A-sam"), agg("B-skill")]}
    a, b = summary["arms"]
    summary["delta"] = {
        "accuracy_pp": round((b["accuracy"] - a["accuracy"]) * 100, 1) if a["accuracy"] is not None and b["accuracy"] is not None else None,
        "calls_saved": a["provider_calls"] - b["provider_calls"],
        "ms_saved": a["total_ms"] - b["total_ms"],
        "bytes_saved": a["total_bytes"] - b["total_bytes"],
    }
    json.dump({"summary": summary, "results": rows, "model": "morriszjm/Tacit-4B-local"}, open(out, "w"), ensure_ascii=False, indent=1)
    print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
    for r in rows:
        print(json.dumps({k: r.get(k) for k in ("id", "arm", "answer", "ref", "correct", "ms", "provider_calls", "precheck", "cache")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
