"""Casos sintéticos para demonstração, não validação clínica."""
import json
from pathlib import Path
import pytest
from app.specialist.engine import infer, load_knowledge_base
ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "knowledge/casos_demonstracao.json").read_text(encoding="utf-8"))
KB = load_knowledge_base(ROOT / "knowledge/rules.json")

@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_synthetic_case(case):
    result = infer(case["answers"], KB)
    assert result.priority == case["expected_priority"]
    assert set(case["expected_rules"]).issubset({r["id"] for r in result.fired_rules})
    assert result.to_dict() == infer(case["answers"], KB).to_dict()
    if case["id"] == "informacao_desconhecida":
        assert result.status == "insufficient"
    if case["id"] == "sem_alerta_coberto":
        assert "Nenhum sinal de alerta coberto" in result.summary

def test_every_rule_has_traceable_sources():
    sources = {s["id"] for s in KB["sources"]}
    for rule in KB["rules"]:
        assert rule["source_ids"]
        assert set(rule["source_ids"]).issubset(sources)
