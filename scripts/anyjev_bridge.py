#!/usr/bin/env python3
# AnyJev bridge — isti /v1/decide ugovor kao `python -m anyjev.serve`, ali radi i s
# Deciderom (bilo koji lokalni model) i Tacitom na transformers engineu (CPU OK).
# Same /v1/decide contract as `python -m anyjev.serve`, but also serves Decider
# (any local model) and Tacit on the transformers engine (CPU-capable).
#
#   pip install "anyjev[hf]"            # bez modela / no models downloaded here
#   python3 scripts/anyjev_bridge.py --model Qwen/Qwen3-4B --mode decider --port 8101
#   python3 scripts/anyjev_bridge.py --model morriszjm/Tacit-4B --mode tacit --port 8101
#
# Nema autentikacije — slušati samo 127.0.0.1. / No auth — bind 127.0.0.1 only.
import argparse
import http.server
import json
import time

KINDS = {"choice": "choice", "yes_no": "noul", "noul": "noul", "score": "score"}


def build_engine(args):
    from anyjev import Decider, Tacit

    if args.mode == "tacit":
        tacit = Tacit.from_pretrained(
            args.model, engine=args.engine, dtype=args.dtype,
            adaptive=args.adaptive, tau=args.tau,
            max_cot_share=None if args.max_cot_share < 0 else args.max_cot_share,
            cot_window=args.cot_window or None, cot_max_tokens=args.cot_max_tokens,
            **({"base_url": args.upstream} if args.upstream else {}),
        )
        return ("tacit", tacit)
    # decider: bilo koji lokalni model / any local model
    if args.engine == "server":
        from anyjev.backends.sglang import SGLangBackend

        backend = SGLangBackend(args.upstream or "http://127.0.0.1:30000", args.model)
    else:
        from anyjev.backends.hf import HFBackend

        backend = HFBackend(args.model, device=args.device, dtype=args.dtype)
    dec = Decider(backend, level="L0")
    return ("decider", dec)


def to_question(Question, item):
    kind = KINDS.get(item.get("kind", "choice"))
    if kind is None:
        raise ValueError("kind must be choice|yes_no|score")
    q, opts = item.get("question", ""), item.get("options")
    if kind == "noul":
        return Question.noul(q)
    if kind == "score":
        if not opts or len(opts) < 2:
            raise ValueError("score needs >=2 levels")
        return Question.score(q, levels=list(opts))
    if not opts or len(opts) < 2:
        raise ValueError("choice needs >=2 options")
    return Question.choice(q, list(opts))


def decide_one(handle, item, state_text):
    from anyjev import Question as Q

    q = to_question(Q, item)
    t0 = time.time()
    if handle[0] == "tacit":
        tacit = handle[1]
        kind = "score" if q.kind == "score" else ("yes_no" if q.kind == "noul" else "choice")
        d = tacit.decide(state=state_text, question=q.text,
                         options=list(q.options) if q.kind != "noul" else None, kind=kind)
        probs = {str(k): float(v) for k, v in d["probs"].items()}
        out = {"answer": d["answer"], "probs": probs, "latency_ms": round((time.time() - t0) * 1000)}
        if isinstance(d.get("answer"), bool):  # yes_no: pin Yes/No ključeve / pin Yes/No keys
            out["probs"] = {"Yes": probs.get("Yes", 0.0), "No": probs.get("No", 0.0)}
        if q.kind == "score":
            out["value"] = float(sum(i * p for i, p in enumerate(probs.values())))
        if d.get("route"):
            out["route"] = d["route"]
        out["level"] = "one_forward" if d.get("route") != "cot" else "cot"
        return out
    dec = handle[1]
    r = dec.decide(state_text, [q])
    d = r[q.id] if q.id in r else list(r)[0]
    dist = {str(k): float(v) for k, v in d.distribution.items()}
    out = {"answer": d.answer if not isinstance(d.answer, bool) else d.answer,
           "probs": dist, "level": d.level,
           "latency_ms": round((time.time() - t0) * 1000)}
    if q.kind == "noul":
        out["probability"] = float(d.p_true)
    if q.kind == "score":
        out["value"] = float(d.value)
    return out


def make_server(handle, model, mode, host, port):
    stats = {"model": model, "mode": mode, "decisions": 0, "errors": 0}

    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"ok": True})
            if self.path == "/v1/stats":
                extra = {}
                try:
                    if mode == "tacit":
                        extra = dict(handle[1].stats)
                except Exception:
                    pass
                return self._send(200, {**stats, **extra})
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/v1/decide":
                return self._send(404, {"error": "not found"})
            try:
                req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                batch = req.get("items") if "items" in req else [req]
                outs = []
                for item in batch:
                    state = item.get("state", "")
                    state_text = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
                    outs.append(decide_one(handle, item, state_text))
                stats["decisions"] += len(outs)
                return self._send(200, {"decisions": outs} if "items" in req else outs[0])
            except (ValueError, KeyError, TypeError) as e:
                stats["errors"] += 1
                return self._send(400, {"error": str(e)})
            except Exception as e:  # model/engine greška -> 502, ne ruši server
                stats["errors"] += 1
                return self._send(502, {"error": str(e)[:500]})

        def log_message(self, fmt, *args):
            pass

    return http.server.ThreadingHTTPServer((host, port), Handler)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="anyjev_bridge.py")
    ap.add_argument("--model", required=True)
    ap.add_argument("--mode", default="tacit", choices=["tacit", "decider"])
    ap.add_argument("--engine", default="transformers", choices=["transformers", "server"])
    ap.add_argument("--upstream", default=None)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8101)
    ap.add_argument("--adaptive", action="store_true")
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--max-cot-share", type=float, default=0.2)
    ap.add_argument("--cot-window", type=int, default=1000)
    ap.add_argument("--cot-max-tokens", type=int, default=8192)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"],
                    help="float32 je brži na CPU bez AVX512/BF16 (kao ovaj server)")
    ap.add_argument("--device", default="cuda",
                    help="placement za Decider HFBackend (ovaj server: cpu)")
    a = ap.parse_args(argv)
    handle = build_engine(a)
    server = make_server(handle, a.model, a.mode, a.host, a.port)
    print("anyjev bridge: http://%s:%d/v1/decide (%s %s)" % (a.host, a.port, a.mode, a.model), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
