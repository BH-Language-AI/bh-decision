# Instalacija u OpenCode / OpenCode installation

1. Zavisnosti (čist checkout): `npm install --prefix packages/decision-mcp` i
   `npm install --prefix packages/opencode-plugin` (`decision-core` nema zavisnosti).
   Provjereno 2026-11-13: `git worktree` + ova dva installa + puni suite zelen (45 TS + 19 Python).
2. Kopiraj skill: `skills/decision-intelligence/` → `.opencode/skills/decision-intelligence/`
   (projektni) ili `~/.config/opencode/skills/` (globalni). OpenCode ga otkriva sam.
2. MCP server — opcija A (preporučeno): instaliraj plugin
   `packages/opencode-plugin` u `plugins` listu `opencode.json`; plugin sam registrira
   lokalni MCP server `bh-decision`. Opcija B (ručno): dodaj u `mcp` sekciju server
   s komandom `node --experimental-strip-types <repo>/packages/decision-mcp/src/index.ts`
   i env `DECISION_CONFIG=<putanja>/decision.json` (JSON u obliku `decision.example.yaml`).
3. Konfiguracija: preko env `DECISION_PROVIDER`, `DECISION_FALLBACK`, `DECISION_ALLOW_PAID`
   (default `false`). Ključevi samo kroz env (`OPENCODE_API_KEY`).
4. Provjera: `/decision-status` komanda ili `decision_status` MCP alat. Ručno: `/decision <zadatak>`, `/decision-risk <zadatak>`, `/decision-rank <zadatak> | opt1, opt2, opt3` (svaka prima `provider=<id>` prefiks za jednokratni izbor).
5. Zahtjevi: Node ≥ 22. Bez modela, GPU-a i plaćenih poziva za instalaciju.
