# Verzije / Tiers: basic vs advanced

Dvije gotove konfiguracije — ista skill/MCP/plugin povrsina, drugi provider ispod.

## Basic — glavni model + Jev-1.13-Free (hosted, $0)

- Konfig: `config/decision.basic.json` (`DECISION_CONFIG=<put>/decision.basic.json`).
- Nista se ne instalira osim `npm install` u paketima; treba samo `OPENCODE_API_KEY`.
- Kada: brzina i nula odrzavanja; podaci (minimalni state) idu vani na hosted endpoint.

## Advanced — lokalni Tacit-4B preko API-ja (CPU, privatno)

- Konfig: `config/decision.advanced.json` (primary `anyjev_local`, fallback `jev`).
- Preduvjet: model `morriszjm/Tacit-4B` (jednokratni download ili postojeci kes) + venv s `anyjev`.
- Start: `scripts/anyjev_serve.sh` (postuje portove/venv/model kroz `ANYJEV_PORT`,
  `ANYJEV_VENV`, `ANYJEV_MODEL`); zdravlje: `curl http://127.0.0.1:8101/health`.
- Kada: nista ne smije van masine; deterministicke bit-za-bit odluke (dokazano rerunom);
  cijena je ~6–17 s po odluci na CPU.
- Adaptive (reasoning za nesigurne) se pali zastavicom na bridgeu (`--adaptive`),
  ne u skillu; na mjerenom setu nije trebao nijednom (cot 0/18).

## Prebacivanje

Samo zamijeni `DECISION_CONFIG` (ili env `DECISION_PROVIDER`/`ANYJEV_*` za jednokratno).
Skill, MCP alati, `/decision*` komande i pragovi ostaju isti u obje verzije.
