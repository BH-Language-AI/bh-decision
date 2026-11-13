#!/usr/bin/env python3
# Generira email-stil HTML izvjestaj iz ab*.json rezultata (isti format kao mailovi).
# Uporaba: python3 scripts/ab_report.py benchmarks/reports/ab4-20261113.json "Naslov" "Podnaslov" [nalazi.txt]
# Nalazi: kratke bullet linije (uz - za rizik/limit) — ako se ne daju, ide genericki tekst.
import html
import json
import sys
from collections import OrderedDict


def esc(x):
    return html.escape(str(x), quote=False)


def main():
    path, title, subtitle = sys.argv[1], sys.argv[2], sys.argv[3]
    findings = []
    if len(sys.argv) > 4:
        findings = [l.strip() for l in open(sys.argv[4], encoding="utf-8") if l.strip()]
    d = json.load(open(path, encoding="utf-8"))
    s = d["summary"]
    a, b = s["arms"]
    dl = s["delta"]
    rows = d["results"]

    def pct(x):
        return f"{x:.1f}%" if isinstance(x, float) else str(x)

    acc_a = f'{a["correct"]}/{a["scored"]} ({a["accuracy"]*100:.1f}%)'
    acc_b = f'{b["correct"]}/{b["scored"]} ({b["accuracy"]*100:.1f}%)'
    dpp = f'{"+" if dl["accuracy_pp"] >= 0 else ""}{dl["accuracy_pp"]} pp'

    batches = OrderedDict()
    for r in rows:
        batches.setdefault(r.get("batch") or "?", []).append(r)

    def agg(rs, arm):
        sc = [r for r in rs if r["arm"] == arm and r.get("ref") is not None and r.get("correct") is not None]
        c = sum(1 for r in sc if r["correct"])
        calls = sum(r["provider_calls"] for r in rs if r["arm"] == arm)
        return c, len(sc), calls

    brow = ""
    bmax = 0
    bdata = []
    for name, rs in batches.items():
        ca, sa, la = agg(rs, "A-sam")
        cb, sb, lb = agg(rs, "B-skill")
        bdata.append((name, ca, sa, cb, sb, la, lb))
        bmax = max(bmax, sa, sb)
    bars = ""
    y = 0
    for name, ca, sa, cb, sb, la, lb in bdata:
        wa = round((ca / bmax) * 330) if bmax else 0
        wb = round((cb / bmax) * 330) if bmax else 0
        bars += (f'<text x="20" y="{y+18}" font-size="12" fill="#334155">{esc(name)} ({sa})</text>'
                 f'<rect x="190" y="{y+4}" width="{wa}" height="13" rx="4" fill="#94a3b8"/>'
                 f'<rect x="190" y="{y+21}" width="{wb}" height="13" rx="4" fill="#0ea5e9"/>')
        y += 46
    H = y + 8
    brow = "".join(
        f'<tr><td style="padding:8px;border:1px solid:#e2e8f0;">{esc(n)}</td>'
        f'<td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;">{ca}/{sa}</td>'
        f'<td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;">{cb}/{sb}</td>'
        f'<td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;">B pozivi: {lb} (A: {la})</td></tr>'
        for n, ca, sa, cb, sb, la, lb in bdata)

    finds = "".join(f"<br>{i+1}) {esc(f)}" for i, f in enumerate(findings)) if findings else \
        "<br>Detalji po grupama u tabeli ispod."
    hb = "".join(f'<div style="flex:1;background:#ecfdf5;border:1px solid:#a7f3d0;border-radius:8px;padding:12px;text-align:center;">'
                 f'<div style="font-size:22px;font-weight:700;color:#047857;">{v}</div>'
                 f'<div style="font-size:12px;color:#065f46;">{k}</div></div>' for k, v in [
                     ("tačnost", f'{dpp} ({a["accuracy"]*100:.1f}% → {b["accuracy"]*100:.1f}%)'),
                     ("pozivi providera", f'−{dl["calls_saved"]} ({a["provider_calls"]} → {b["provider_calls"]})'),
                     ("vrijeme", f'−{dl["ms_saved"]} ms'),
                     ("bajtovi", f'−{dl["bytes_saved"]} ({a["total_bytes"]} → {b["total_bytes"]})')])

    out = f"""<!DOCTYPE html>
<html lang="bs">
<head>
<meta charset="UTF-8">
<title>BH-Decision — {esc(title)}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;color:#1e293b;">
<div style="max-width:680px;margin:0 auto;background:#ffffff;">
  <div style="background:#0f172a;color:#fff;padding:28px 32px;">
    <div style="font-size:12px;letter-spacing:2px;color:#94a3b8;">BH-DECISION &middot; A/B TEST</div>
    <h1 style="margin:8px 0 4px;font-size:24px;">{esc(title)}</h1>
    <div style="color:#cbd1d8;font-size:14px;">{esc(subtitle)}</div>
  </div>
  <div style="padding:24px 32px;">
    <div style="display:flex;gap:12px;margin-bottom:20px;">{hb}</div>
    <h2 style="font-size:17px;border-bottom:2px solid:#0ea5e9;padding-bottom:6px;">&#9679; Uporedna tabela po KPI</h2>
    <table style="width:100%;border-collapse:collapse;font-size:14px;margin:12px 0 20px;">
      <tr style="background:#0f172a;color:#fff;">
        <th style="padding:8px;text-align:left;">KPI</th><th style="padding:8px;">A: model sam</th><th style="padding:8px;">B: model + skill</th><th style="padding:8px;">Razlika</th>
      </tr>
      <tr style="background:#f8fafc;">
        <td style="padding:8px;border:1px solid:#e2e8f0;"><b>Tačnost</b></td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;">{acc_a}</td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;"><b>{acc_b}</b></td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;color:#047857;"><b>{dpp}</b></td>
      </tr>
      <tr>
        <td style="padding:8px;border:1px solid:#e2e8f0;"><b>Pozivi providera</b></td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;">{a["provider_calls"]}</td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;"><b>{b["provider_calls"]}</b></td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;color:#047857;"><b>−{dl["calls_saved"]} (precheck {b["precheck_hits"]} + keš {b["cache_hits"]})</b></td>
      </tr>
      <tr style="background:#f8fafc;">
        <td style="padding:8px;border:1px solid:#e2e8f0;"><b>Ukupno vrijeme</b></td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;">{a["total_ms"]} ms (prosjek {a["avg_ms"]})</td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;"><b>{b["total_ms"]} ms (prosjek {b["avg_ms"]})</b></td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;color:#047857;"><b>−{dl["ms_saved"]} ms</b></td>
      </tr>
      <tr>
        <td style="padding:8px;border:1px solid:#e2e8f0;"><b>Protok (bajtovi)</b></td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;">{a["total_bytes"]} (~{a["est_tokens"]} tokena*)</td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;"><b>{b["total_bytes"]} (~{b["est_tokens"]} tokena*)</b></td>
        <td style="padding:8px;border:1px solid:#e2e8f0;text-align:center;color:#047857;"><b>−{dl["bytes_saved"]}</b></td>
      </tr>
    </table>
    <div style="font-size:12px;color:#64748b;margin:-12px 0 20px;">*Tokeni su procjena (bajtovi/4); pozivi, ms i bajtovi su tačno izmjereni.</div>
    <h3 style="font-size:14px;margin:16px 0 8px;">Tačnost po grupama, bodovani zadaci (siva=A, plava=B)</h3>
    <svg width="100%" viewBox="0 0 600 {H}" style="background:#f8fafc;border:1px solid:#e2e8f0;border-radius:8px;">{bars}</svg>
    <table style="width:100%;border-collapse:collapse;font-size:14px;margin:12px 0 20px;">
      <tr style="background:#0f172a;color:#fff;"><th style="padding:8px;text-align:left;">Grupa</th><th style="padding:8px;">A</th><th style="padding:8px;">B</th><th style="padding:8px;">Pozivi</th></tr>
      {brow}
    </table>
    <div style="background:#fffbeb;border:1px solid:#fcd34d;border-radius:8px;padding:12px;font-size:14px;margin-bottom:20px;">
      <b>&#9679; Nalazi:</b>{finds}
    </div>
    <h2 style="font-size:17px;border-bottom:2px solid:#0ea5e9;padding-bottom:6px;">&#9679; Metodologija i ograničenja</h2>
    <ul style="font-size:14px;line-height:1.7;margin:12px 0 20px;padding-left:20px;">
      <li>Isti model, isti zadaci, isti dan — jedina razlika je skill politika (precheck → keš → model + pragovi).</li>
      <li>Jedan run — indikacija, ne garancija; tokeni su procjena; sirovi JSON uz izvještaj.</li>
    </ul>
    <div style="font-size:12px;color:#94a3b8;text-align:center;">BH-Decision &middot; Kolektiv d.o.o. + Gamatrade d.o.o. &middot; generirano 13.11.2026.</div>
  </div>
</div>
</body>
</html>
"""
    outpath = path.replace(".json", ".html")
    open(outpath, "w", encoding="utf-8").write(out)
    print("napisano:", outpath)


if __name__ == "__main__":
    main()
