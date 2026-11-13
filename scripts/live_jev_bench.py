#!/usr/bin/env python3
# Route A runner: scenariji -> Jev-1.13-Free SystemOne endpoint -> results JSON.
# Stdlib + curl (endpoint filtrira urllib klijente, curl prolazi).
# Kljuc samo iz env OPENCODE_API_KEY, nikad u logove ni u izlaz.
import json
import subprocess
import sys
import time

ENDPOINT = "https://opencode.ai/inference/systemone/v1/systemone"
MODEL = "jev-1.13-free"


def post(payload, key, timeout):
    t0 = time.time()
    p = subprocess.run(
        ["curl", "-sS", "-m", str(timeout), "-X", "POST", ENDPOINT,
         "-H", "Content-Type: application/json",
         "-H", "Authorization: Bearer " + key,
         "-d", json.dumps(payload)],
        capture_output=True, text=True)
    ms = round((time.time() - t0) * 1000)
    if p.returncode != 0:
        return -1, {"error": p.stderr[:200]}, ms
    try:
        return 200, json.loads(p.stdout or "{}"), ms
    except Exception:
        return -1, {"error": (p.stdout or "")[:200]}, ms


def main():
    scenarios, out = sys.argv[1], sys.argv[2]
    spacing, timeout, label = float(sys.argv[3]) if len(sys.argv) > 3 else 10, \
        sys.argv[4] if len(sys.argv) > 4 else "60", sys.argv[5] if len(sys.argv) > 5 else "jev-free-live"
    import os
    key = os.environ.get("OPENCODE_API_KEY", "")
    if not key:
        sys.exit("OPENCODE_API_KEY missing")
    results = []
    lines = [json.loads(x) for x in open(scenarios) if x.strip()]
    for i, s in enumerate(lines):
        q = {"instructions": s["question"]}
        if s["kind"] == "yes_no":
            q["type"] = "noul"
        else:
            q["type"] = "choice"
            q["criteria"] = s["options"]
        st, body, ms = post({"model": MODEL, "state": {"task": s["state"], "language": s["lang"]},
                             "questions": {"q": q}}, key, timeout)
        rec = {"id": s["id"], "lang": s["lang"], "kind": s["kind"], "reference": s.get("reference"),
               "http": st, "latency_ms": ms}
        ans = (body.get("answers") or {}).get("q") if st == 200 and isinstance(body, dict) else None
        if isinstance(ans, dict):
            rec["model_version"] = body.get("model", MODEL)
            if s["kind"] == "yes_no" and isinstance(ans.get("noul"), (int, float)):
                rec["answer"] = ans["noul"]
                if s.get("reference") is not None:
                    rec["correct"] = ((ans["noul"] >= 0.5) == bool(s["reference"]))
            elif isinstance(ans.get("choice"), str):
                rec["answer"] = ans["choice"]
                rec["probs"] = ans.get("probabilities")
                rec["confidence"] = ans.get("confidence")
                if s.get("reference") is not None:
                    rec["correct"] = (str(ans["choice"]) == str(s["reference"]))
            else:
                rec["error"] = "bad answer shape"
        else:
            rec["error"] = body.get("error", body)
        results.append(rec)
        print(json.dumps({k: rec.get(k) for k in ("id", "answer", "reference", "correct", "latency_ms", "error")},
                         ensure_ascii=False), flush=True)
        if i < len(lines) - 1:
            time.sleep(spacing)
    lat = sorted(r["latency_ms"] for r in results)
    summary = {"label": label, "n": len(results),
               "errors": sum(1 for r in results if "error" in r or r["http"] != 200),
               "scored": sum(1 for r in results if r.get("reference") is not None and "correct" in r),
               "correct": sum(1 for r in results if r.get("correct")),
               "lat_p50": lat[len(lat) // 2] if lat else None,
               "lat_max": max(lat) if lat else None}
    json.dump({"summary": summary, "results": results}, open(out, "w"), ensure_ascii=False, indent=1)
    print("SUMMARY " + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
