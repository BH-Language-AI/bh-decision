"""BH-Decision DI GPU bench — Tacit-4B na Kaggle GPU (B/C/D) + pokušaj Clef-Flash (E).

GPU + internet kernel. Modeli se skidaju s HF (javni, bez tokena).
Scenariji: ista datoteka kao lokalno (pinani commit).
Rezultat: /kaggle/working/output/di-gpu-bench.json + sažetak u logu.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

COMMIT = "393f1f7"
SCEN_URL = ("https://raw.githubusercontent.com/BH-Language-AI/bh-decision/"
            f"{COMMIT}/benchmarks/scenarios/anyjev-live.jsonl")
OUT = "/kaggle/working/output"
os.makedirs(OUT, exist_ok=True)

print("cuda:", __import__("torch").cuda.is_available(),
      __import__("torch").cuda.get_device_name(0), flush=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "anyjev"],
               check=True)
from anyjev import Decider, Tacit  # noqa: E402
from anyjev.backends.hf import HFBackend  # noqa: E402

scen = [json.loads(l) for l in
        urllib.request.urlopen(SCEN_URL, timeout=60).read().decode().splitlines()
        if l.strip()]
print("scenarija:", len(scen), flush=True)

model = "morriszjm/Tacit-4B"


def run_tacit(**kw):
    t = Tacit.from_pretrained(model, engine="transformers", **kw)
    res = []
    for s in scen:
        kind = "score" if s["kind"] == "score" else ("yes_no" if s["kind"] == "yes_no" else "choice")
        t0 = time.time()
        try:
            d = t.decide(state=s["state"], question=s["question"],
                         options=list(s["options"].keys()) if s.get("options") else None,
                         kind=kind)
            ms = round((time.time() - t0) * 1000)
            ans = d["answer"]
            rec = {"id": s["id"], "answer": ans,
                   "probs": {str(k): float(v) for k, v in d["probs"].items()},
                   "route": d.get("route"), "latency_ms": ms}
            if s.get("reference") is not None:
                ref = s["reference"]
                a = "Yes" if ans is True else ("No" if ans is False else ans)
                r = "Yes" if ref is True else ("No" if ref is False else ref)
                rec["correct"] = (str(a) == str(r))
        except Exception as e:  # noqa: BLE001
            rec = {"id": s["id"], "error": str(e)[:200],
                   "latency_ms": round((time.time() - t0) * 1000)}
        res.append(rec)
        print(json.dumps({k: rec.get(k) for k in ("id", "answer", "correct", "latency_ms", "route", "error")}),
              flush=True)
    return res


def summarize(res, label):
    scored = [r for r in res if "correct" in r]
    lat = sorted(r["latency_ms"] for r in res)
    s = {"label": label, "n": len(res),
         "errors": sum(1 for r in res if "error" in r),
         "scored": len(scored),
         "correct": sum(1 for r in scored if r["correct"]),
         "lat_p50": lat[len(lat) // 2], "lat_max": lat[-1],
         "cot": sum(1 for r in res if r.get("route") == "cot")}
    print("SUMMARY " + json.dumps(s, ensure_ascii=False), flush=True)
    return s


all_res = {}
all_res["C-tacit-l0-gpu"] = run_tacit()
all_res["D-tacit-adaptive-gpu"] = run_tacit(adaptive=True)
print("--- Decider L0 (iste težine) ---", flush=True)
dec = Decider(HFBackend(model, device="cuda", dtype="bfloat16"), level="L0")
bres = []
from anyjev import Question  # noqa: E402
for s in scen:
    if s["kind"] == "choice":
        q = Question.choice(s["question"], list(s["options"].keys()))
    elif s["kind"] == "yes_no":
        q = Question.noul(s["question"])
    else:
        q = Question.score(s["question"], levels=list(s["options"].keys()))
    t0 = time.time()
    try:
        d = dec.decide(s["state"], [q])[q.id]
        ms = round((time.time() - t0) * 1000)
        ans = d.answer
        rec = {"id": s["id"], "answer": ans,
               "probs": {str(k): float(v) for k, v in d.distribution.items()},
               "level": d.level, "latency_ms": ms}
        if s.get("reference") is not None:
            ref = s["reference"]
            a = "Yes" if ans is True else ("No" if ans is False else ans)
            r = "Yes" if ref is True else ("No" if ref is False else ref)
            rec["correct"] = (str(a) == str(r))
    except Exception as e:  # noqa: BLE001
        rec = {"id": s["id"], "error": str(e)[:200],
               "latency_ms": round((time.time() - t0) * 1000)}
    bres.append(rec)
    print(json.dumps({k: rec.get(k) for k in ("id", "answer", "correct", "latency_ms", "error")}),
          flush=True)
all_res["B-decider-l0-gpu"] = bres

# --- E: Clef-Flash, samo ako ima diska; inače iskren blok ---
free_gb = shutil.disk_usage("/kaggle/working").free / 1e9
print(f"slobodno na /kaggle/working: {free_gb:.1f} GB", flush=True)
all_res["E-clef"] = {"skipped": None, "free_gb": round(free_gb, 1)}
if free_gb > 25:
    try:
        from huggingface_hub import snapshot_download
        p = snapshot_download("Cloudflare/clef-flash")
        sys.path.insert(0, p)
        from joint_schema_model import collate_records, encode_record, load_release_model
        import torch
        m, proc = load_release_model(p, device="cuda")
        eres = []
        for s in scen:
            kind = {"choice": "choice", "yes_no": "noul"}.get(s["kind"], "score")
            rec_q = {"state": s["state"], "questions": {
                "q": {"type": kind,
                      **({"instructions": s["question"]} if True else {}),
                      **({"criteria": s["options"]} if s.get("options") and kind == "choice" else {}),
                      **({"criteria": list(s["options"].keys())} if s.get("options") and kind == "score" else {})}}}
            t0 = time.time()
            try:
                with torch.inference_mode():
                    enc = encode_record(proc.tokenizer, rec_q, processor=proc)
                    batch = collate_records([enc], proc.tokenizer.pad_token_id, torch.device("cuda"))
                    logits = m(batch)[0]
                import torch as _t
                probs = logits[0].float().softmax(-1).tolist()
                opts = (list(s["options"].keys()) if s.get("options") else ["No", "Yes"])
                ms = round((time.time() - t0) * 1000)
                best = opts[int(_t.tensor(probs).argmax())]
                rec = {"id": s["id"], "answer": best,
                       "probs": dict(zip(opts, probs)), "latency_ms": ms}
                if s.get("reference") is not None:
                    rec["correct"] = (str(best) == str(s["reference"]))
            except Exception as e:  # noqa: BLE001
                rec = {"id": s["id"], "error": str(e)[:300],
                       "latency_ms": round((time.time() - t0) * 1000)}
            eres.append(rec)
            print(json.dumps({k: rec.get(k) for k in ("id", "answer", "correct", "latency_ms", "error")}),
                  flush=True)
        all_res["E-clef"] = {"results": eres, "free_gb": round(free_gb, 1)}
    except Exception as e:  # noqa: BLE001
        all_res["E-clef"] = {"error": str(e)[:500], "free_gb": round(free_gb, 1)}
        print("E-CLEF-BLOKIRAN:", str(e)[:300], flush=True)
else:
    print(f"E-CLEF preskočen: samo {free_gb:.1f} GB slobodno (treba ~20 GB)", flush=True)

summaries = {k: summarize(v, k) for k, v in all_res.items() if isinstance(v, list)}
if isinstance(all_res["E-clef"], dict) and "results" in all_res["E-clef"]:
    summaries["E-clef-gpu"] = summarize(all_res["E-clef"]["results"], "E-clef-gpu")
json.dump({"summaries": summaries, "results": all_res},
          open(f"{OUT}/di-gpu-bench.json", "w"), ensure_ascii=False, indent=1)
print("GOTOVO:", f"{OUT}/di-gpu-bench.json", flush=True)
