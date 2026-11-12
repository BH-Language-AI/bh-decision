#!/usr/bin/env python3
# Live benchmark runner: scenariji -> bridge/gateway HTTP -> results JSON.
# Nema ovisnosti osim stdlib. Bez fabriciranja: zapisuje samo izmjerene odgovore.
import json
import sys
import time
import urllib.request


def post(url, obj, timeout):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}"), round((time.time() - t0) * 1000)
    except Exception as e:
        return -1, {"error": str(e)[:200]}, round((time.time() - t0) * 1000)


def main():
    base, scenarios, out, timeout, label = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
    base = base.rstrip("/")
    results = []
    lines = [json.loads(x) for x in open(scenarios) if x.strip()]
    for s in lines:
        item = {"state": s["state"], "question": s["question"], "kind": s["kind"]}
        if s.get("options"):
            item["options"] = list(s["options"].keys())
        st, body, ms = post(base + "/v1/decide", item, timeout)
        rec = {"id": s["id"], "lang": s["lang"], "kind": s["kind"], "reference": s.get("reference"),
               "http": st, "latency_ms": ms}
        if st == 200 and isinstance(body, dict):
            rec["answer"] = body.get("answer")
            rec["probs"] = body.get("probs")
            rec["route"] = body.get("route")
            if s.get("reference") is not None:
                rec["correct"] = (str(body.get("answer")) == str(s["reference"]))
        else:
            rec["error"] = body.get("error", body)
        results.append(rec)
        print(json.dumps({k: rec.get(k) for k in ("id", "answer", "reference", "correct", "latency_ms", "route", "error")}),
              flush=True)
    summary = {"label": label, "n": len(results),
               "errors": sum(1 for r in results if "error" in r or r["http"] != 200),
               "scored": sum(1 for r in results if r.get("reference") is not None and "correct" in r),
               "correct": sum(1 for r in results if r.get("correct")),
               "lat_p50": sorted(r["latency_ms"] for r in results)[len(results) // 2] if results else None,
               "lat_max": max((r["latency_ms"] for r in results), default=None),
               "cot": sum(1 for r in results if r.get("route") == "cot")}
    json.dump({"summary": summary, "results": results}, open(out, "w"), ensure_ascii=False, indent=1)
    print("SUMMARY " + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
