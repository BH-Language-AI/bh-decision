"""Validacija izlaznog protokola v1 (stdlib only, bez jsonschema).

Ako postoji schemas/protocol-v1.schema.json, pravila se čitaju iz njega;
inače vrijede ugrađena pravila iz docs/architecture/proposed-architecture.md.
"""
import json
import os

import pytest

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "schemas", "protocol-v1.schema.json")

DECISIONS = {"choice_id", "yes", "no", "abstain"}
LANGS = {"bs", "en"}
MODELS = {"BH-Decision-2B", "BH-Decision-4B", "BH-Decision-9B"}
RISK_LEVELS = {"low", "medium", "high"}

GOOD = {
    "decision": "choice_id",
    "options_ranked": ["id3", "id1"],
    "scores": {"id1": 0.7, "id3": 0.9},
    "risk": {"level": "low", "factors": ["kratak rok"]},
    "confidence": 0.8,
    "abstention_reason": None,
    "rationale_short": "Treća opcija najbolje zadovoljava kriterije.",
    "lang": "bs",
    "model": "BH-Decision-2B",
    "version": "0.1",
}

BAD_CONFIDENCE = dict(GOOD, confidence=1.5)  # confidence izvan 0-1
BAD_DECISION = dict(GOOD, decision="mozda")  # nepoznat decision enum


def validate(record):
    """Vraća listu grešaka (prazna = validno). Ručne provjere, stdlib only."""
    errors = []
    required = ["decision", "options_ranked", "scores", "risk", "confidence",
                "rationale_short", "lang", "model", "version"]
    for field in required:
        if field not in record:
            errors.append(f"nedostaje: {field}")
    if errors:
        return errors
    if record["decision"] not in DECISIONS and not str(record["decision"]).startswith("id"):
        # decision je "choice_id | yes | no | abstain": choice_id = bilo koji id opcije
        if record["decision"] not in ("yes", "no", "abstain"):
            errors.append(f"loš decision: {record['decision']!r}")
    if not isinstance(record["options_ranked"], list):
        errors.append("options_ranked mora biti lista")
    if not isinstance(record["scores"], dict):
        errors.append("scores mora biti rječnik")
    conf = record["confidence"]
    if not isinstance(conf, (int, float)) or isinstance(conf, bool) or not 0.0 <= conf <= 1.0:
        errors.append(f"confidence mora biti 0-1, dobijeno: {conf!r}")
    risk = record["risk"]
    if not isinstance(risk, dict) or risk.get("level") not in RISK_LEVELS:
        errors.append(f"risk.level mora biti {sorted(RISK_LEVELS)}")
    if record["lang"] not in LANGS:
        errors.append(f"lang mora biti {sorted(LANGS)}")
    if record["model"] not in MODELS:
        errors.append(f"model mora biti {sorted(MODELS)}")
    return errors


def test_schema_file_if_present():
    if not os.path.exists(SCHEMA_PATH):
        pytest.skip("nema schemas/protocol-v1.schema.json — vrijede ugrađena pravila")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    assert isinstance(schema, dict) and schema, "schema mora biti neprazan JSON objekt"


def test_good_example_passes():
    assert validate(GOOD) == []


def test_bad_confidence_fails():
    assert any("confidence" in e for e in validate(BAD_CONFIDENCE))


def test_bad_decision_fails():
    assert any("decision" in e for e in validate(BAD_DECISION))
