"""BH-Decision E: Clef-Flash lokalno na Kaggle GPU (T4 16GB).

Pokušaj s device_map=auto + CPU offload + fp16 (18GB BF16 ne stane u 16GB VRAM).
Ako padne: iskren blok s izmjerenim brojkama, bez nagađanja.
Izlaz: /kaggle/working/output/di-clef-bench.json + SUMMARY u logu.
"""
import json
import os
import shutil
import sys
import time
import urllib.request

COMMIT = "393f1f7"
SCEN_URL = ("https://raw.githubusercontent.com/BH-Language-AI/bh-decision/"
            f"{COMMIT}/benchmarks/scenarios/anyjev-live.jsonl")
OUT = "/kaggle/working/output"
os.makedirs(OUT, exist_ok=True)

import torch  # noqa: E402

print("cuda:", torch.cuda.is_available(), torch.cuda.get_device_name(0),
      f"vram={torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB", flush=True)
free_gb = shutil.disk_usage("/kaggle/working").free / 1e9
print(f"disk free: {free_gb:.1f} GB", flush=True)

scen = [json.loads(l) for l in
        urllib.request.urlopen(SCEN_URL, timeout=60).read().decode().splitlines()
        if l.strip()]

rec = {"gpu": torch.cuda.get_device_name(0), "free_gb": round(free_gb, 1)}
if free_gb < 19:
    rec["skipped"] = f"samo {free_gb:.1f} GB slobodno (treba ~19 GB)"
    print("E-CLEF preskočen: premalo diska", flush=True)
else:
    try:
        from huggingface_hub import snapshot_download
        p = snapshot_download("Cloudflare/clef-flash")
        sys.path.insert(0, p)
        from joint_schema_model import (collate_records, encode_record,
                                        load_release_model)
        t0 = time.time()
        model, proc = load_release_model(
            p, device="cuda", dtype=torch.float16,
            device_map="auto",
            max_memory={0: "14GiB", "cpu": "32GiB"},
            offload_folder="/kaggle/working/offload")
        print(f"load: {round(time.time() - t0, 1)}s", flush=True)
        res = []
        for s in scen:
            kind = {"choice": "choice", "yes_no": "noul"}.get(s["kind"], "score")
            q = {"type": kind, "instructions": s["question"]}
            if kind == "choice":
                q["criteria"] = s["options"]
            elif kind == "score":
                q["criteria"] = list(s["options"].keys())
            t0 = time.time()
            try:
                with torch.inference_mode():
                    enc = encode_record(proc.tokenizer, {"state": s["state"], "questions": {"q": q}},
                                        processor=proc)
                    batch = collate_records([enc], proc.tokenizer.pad_token_id,
                                            torch.device("cuda"))
                    logits = model(batch)[0]
                import torch as _t
                pr = logits[0].float().softmax(-1).tolist()
                opts = (list(s["options"].keys()) if s.get("options") else ["No", "Yes"])
                best = opts[int(_t.tensor(pr).argmax())]
                r = {"id": s["id"], "answer": best, "probs": dict(zip(opts, pr)),
                     "latency_ms": round((time.time() - t0) * 1000)}
                if s.get("reference") is not None:
                    ref = s["reference"]
                    r["correct"] = (str(best) == str("Yes" if ref is True else ref))
            except Exception as e:  # noqa: BLE001
                r = {"id": s["id"], "error": str(e)[:300],
                     "latency_ms": round((time.time() - t0) * 1000)}
            res.append(r)
            print(json.dumps({k: r.get(k) for k in ("id", "answer", "correct", "latency_ms", "error")}),
                  flush=True)
        scored = [r for r in res if "correct" in r]
        lat = sorted(r["latency_ms"] for r in res)
        rec["summary"] = {"n": len(res),
                          "errors": sum(1 for r in res if "error" in r),
                          "scored": len(scored),
                          "correct": sum(1 for r in scored if r["correct"]),
                          "lat_p50": lat[len(lat) // 2], "lat_max": lat[-1]}
        rec["results"] = res
        print("SUMMARY " + json.dumps(rec["summary"], ensure_ascii=False), flush=True)
    except Exception as e:  # noqa: BLE001
        rec["error"] = str(e)[:500]
        print("E-CLEF-BLOKIRAN:", str(e)[:300], flush=True)

json.dump(rec, open(f"{OUT}/di-clef-bench.json", "w"), ensure_ascii=False, indent=1)
print("GOTOVO:", f"{OUT}/di-clef-bench.json", flush=True)
