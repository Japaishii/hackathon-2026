"""Small forward-chaining engine for explicit JSON production rules.

Unknown values are never coerced to False. Rule conditions support ``all``,
``any`` and typed ``equals`` clauses. Facts are immutable inputs; conclusions
are maintained in a per-assessment working memory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class KnowledgeBaseError(ValueError):
    """Raised when a knowledge base is malformed or internally inconsistent."""


@dataclass(frozen=True)
class InferenceResult:
    knowledge_base_version: str
    priority: str
    status: str
    summary: str
    conclusions: list[dict[str, Any]]
    fired_rules: list[dict[str, Any]]
    unknowns: list[str]
    guidance: list[str]
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_base_version": self.knowledge_base_version,
            "priority": self.priority,
            "status": self.status,
            "summary": self.summary,
            "conclusions": self.conclusions,
            "fired_rules": self.fired_rules,
            "unknowns": self.unknowns,
            "guidance": self.guidance,
            "disclaimer": self.disclaimer,
        }


def load_knowledge_base(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeBaseError(f"Não foi possível ler a base de conhecimento: {exc}") from exc
    validate_knowledge_base(data)
    return data


def validate_knowledge_base(data: dict[str, Any]) -> None:
    if not isinstance(data, dict) or not data.get("version"):
        raise KnowledgeBaseError("A base precisa informar uma versão.")
    questions = data.get("questions", [])
    question_ids = {q.get("id") for q in questions if isinstance(q, dict)} if questions else set(data.get("fact_ids", []))
    if questions and len(question_ids) != len(questions):
        raise KnowledgeBaseError("Identificadores de pergunta ausentes ou duplicados.")
    if not question_ids:
        raise KnowledgeBaseError("A base precisa declarar perguntas ou fact_ids.")
    seen: set[str] = set()
    for rule in data.get("rules", []):
        rid = rule.get("id")
        if not rid or rid in seen:
            raise KnowledgeBaseError(f"Identificador de regra ausente ou duplicado: {rid}")
        seen.add(rid)
        if rule.get("priority") not in data.get("priority_order", []):
            raise KnowledgeBaseError(f"Prioridade inválida na regra {rid}.")
        clauses = rule.get("when", {})
        if not any(key in clauses for key in ("all", "any", "equals")):
            raise KnowledgeBaseError(f"Regra {rid} sem condições suportadas.")
        for clause in clauses.get("all", []) + clauses.get("any", []):
            if clause.get("fact") not in question_ids:
                raise KnowledgeBaseError(f"Fato desconhecido na regra {rid}: {clause.get('fact')}")
        for fact in clauses.get("equals", {}):
            if fact not in question_ids:
                raise KnowledgeBaseError(f"Fato desconhecido na regra {rid}: {fact}")


def _matches(rule: dict[str, Any], facts: dict[str, Any]) -> bool:
    when = rule["when"]

    def is_true(clause: dict[str, Any]) -> bool:
        return facts.get(clause["fact"]) is clause.get("is", True)

    required = when.get("all", [])
    alternatives = when.get("any", [])
    equalities = when.get("equals", {})
    if required and not all(is_true(clause) for clause in required):
        return False
    if alternatives and not any(is_true(clause) for clause in alternatives):
        return False
    if any(facts.get(key) != value for key, value in equalities.items()):
        return False
    return True


def infer(facts: dict[str, Any], knowledge_base: dict[str, Any]) -> InferenceResult:
    """Run rules to a fixed point and return a stable explanation trace."""
    validate_knowledge_base(knowledge_base)
    question_ids = {q["id"] for q in knowledge_base["questions"]} if knowledge_base.get("questions") else set(knowledge_base["fact_ids"])
    normalized = {key: value for key, value in facts.items() if key in question_ids}
    unknowns = sorted(key for key in question_ids if key not in normalized or normalized[key] is None)
    fired: list[dict[str, Any]] = []
    conclusions: list[dict[str, Any]] = []
    seen: set[str] = set()
    working_facts = dict(normalized)

    # Rules may add boolean derived facts; monotonic firing plus the seen set
    # prevents duplicate activations and loops.
    changed = True
    while changed:
        changed = False
        for rule in knowledge_base["rules"]:
            if rule["id"] in seen or not _matches(rule, working_facts):
                continue
            seen.add(rule["id"])
            fired.append({"id": rule["id"], "label": rule["label"], "because": rule["because"], "source_ids": rule.get("source_ids", [])})
            conclusion = {"id": rule["conclusion"], "label": rule["conclusion_label"], "priority": rule["priority"], "rule_id": rule["id"]}
            conclusions.append(conclusion)
            if rule.get("derive") and working_facts.get(rule["derive"]) is not True:
                working_facts[rule["derive"]] = True
                changed = True

    priorities = knowledge_base["priority_order"]
    priority = min((item["priority"] for item in conclusions), key=priorities.index) if conclusions else "none"
    minimum_facts = knowledge_base.get("required_for_clear_result", [])
    insufficient = any(key not in normalized or normalized[key] is None for key in minimum_facts)
    status = "insufficient" if insufficient else "evaluated"
    if conclusions:
        summary = knowledge_base["priority_labels"][priority]
    elif insufficient:
        summary = "Informações insuficientes para verificar todos os sinais prioritários."
    else:
        summary = "Nenhum sinal de alerta coberto por esta versão das regras foi identificado."
    guidance = list(knowledge_base.get("default_guidance", []))
    if conclusions:
        guidance = list(dict.fromkeys(guidance + [rule.get("guidance", "") for rule in knowledge_base["rules"] if rule["id"] in seen and rule.get("guidance")]))
    if insufficient:
        guidance.append("Complete as respostas desconhecidas quando for seguro fazê-lo e procure orientação veterinária se houver preocupação.")
    return InferenceResult(
        knowledge_base_version=knowledge_base["version"], priority=priority, status=status,
        summary=summary, conclusions=conclusions, fired_rules=fired, unknowns=unknowns,
        guidance=guidance, disclaimer=knowledge_base["disclaimer"],
    )
