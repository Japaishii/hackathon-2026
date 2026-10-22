
"""Motor de inferência do BoviHealth.

Sistema especialista baseado em regras explícitas.

Características:
- Encadeamento para frente.
- Regras determinísticas.
- Tratamento de informações desconhecidas.
- Priorização dos sinais de alerta.
- Rastreabilidade das regras acionadas.
- Consolidação das orientações repetitivas.

O sistema realiza triagem e não substitui
a avaliação de um médico-veterinário.
"""

from __future__ import annotations

import json
import re
import unicodedata

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class KnowledgeBaseError(ValueError):
    """Erro na estrutura da base de conhecimento."""


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


# =====================================================
# BASE DE CONHECIMENTO
# =====================================================

def load_knowledge_base(path: Path) -> dict[str, Any]:
    """Carrega e valida a base de conhecimento."""

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeBaseError(
            "Não foi possível ler a base de conhecimento: "
            f"{exc}"
        ) from exc

    validate_knowledge_base(data)

    return data


def validate_knowledge_base(data: dict[str, Any]) -> None:
    """Verifica a consistência estrutural das regras."""

    if not isinstance(data, dict) or not data.get("version"):
        raise KnowledgeBaseError(
            "A base precisa informar uma versão."
        )

    questions = data.get("questions", [])

    if questions:
        question_ids = {
            q.get("id")
            for q in questions
            if isinstance(q, dict)
        }
    else:
        question_ids = set(data.get("fact_ids", []))

    if questions and len(question_ids) != len(questions):
        raise KnowledgeBaseError(
            "Identificadores de pergunta ausentes "
            "ou duplicados."
        )

    if not question_ids:
        raise KnowledgeBaseError(
            "A base precisa declarar perguntas ou fact_ids."
        )

    sources = data.get("sources", [])

    source_ids = {
        source.get("id")
        for source in sources
    }

    if len(source_ids) != len(sources) or None in source_ids:
        raise KnowledgeBaseError(
            "Fontes duplicadas ou sem identificador."
        )

    priority_order = data.get("priority_order", [])

    if len(priority_order) != len(set(priority_order)):
        raise KnowledgeBaseError(
            "Prioridades duplicadas."
        )

    seen: set[str] = set()

    for rule in data.get("rules", []):
        rid = rule.get("id")

        if not rid or rid in seen:
            raise KnowledgeBaseError(
                "Identificador de regra ausente "
                f"ou duplicado: {rid}"
            )

        seen.add(rid)

        if rule.get("priority") not in priority_order:
            raise KnowledgeBaseError(
                f"Prioridade inválida na regra {rid}."
            )

        rule_sources = rule.get("source_ids", [])

        if (
            not rule_sources
            or any(
                sid not in source_ids
                for sid in rule_sources
            )
        ):
            raise KnowledgeBaseError(
                f"Regra {rid} sem fontes válidas cadastradas."
            )

        clauses = rule.get("when", {})

        supported = (
            "all",
            "any",
            "any_systemic",
            "equals",
        )

        if not any(key in clauses for key in supported):
            raise KnowledgeBaseError(
                f"Regra {rid} sem condições suportadas."
            )

        condition_lists = (
            clauses.get("all", [])
            + clauses.get("any", [])
            + clauses.get("any_systemic", [])
        )

        for clause in condition_lists:
            if (
                not isinstance(clause, dict)
                or "fact" not in clause
            ):
                raise KnowledgeBaseError(
                    f"Cláusula inválida na regra {rid}."
                )

            if clause["fact"] not in question_ids:
                raise KnowledgeBaseError(
                    f"Fato desconhecido na regra {rid}: "
                    f"{clause['fact']}"
                )

        for fact in clauses.get("equals", {}):
            if fact not in question_ids:
                raise KnowledgeBaseError(
                    f"Fato desconhecido na regra {rid}: {fact}"
                )


# =====================================================
# VERIFICAÇÃO DAS CONDIÇÕES
# =====================================================

def _matches(
    rule: dict[str, Any],
    facts: dict[str, Any],
) -> bool:
    """Verifica se uma regra pode ser acionada."""

    when = rule["when"]

    def is_true(clause: dict[str, Any]) -> bool:
        expected = clause.get("is", True)
        actual = facts.get(clause["fact"])

        # Não transformar informação desconhecida
        # em uma resposta negativa.
        if actual is None:
            return False

        return (
            type(actual) is type(expected)
            and actual == expected
        )

    required = when.get("all", [])
    alternatives = when.get("any", [])
    systemic = when.get("any_systemic", [])
    equalities = when.get("equals", {})

    if required and not all(
        is_true(clause)
        for clause in required
    ):
        return False

    if alternatives and not any(
        is_true(clause)
        for clause in alternatives
    ):
        return False

    if systemic and not any(
        is_true(clause)
        for clause in systemic
    ):
        return False

    for key, expected in equalities.items():
        actual = facts.get(key)

        if (
            actual is None
            or type(actual) is not type(expected)
            or actual != expected
        ):
            return False

    return True


# =====================================================
# ORGANIZAÇÃO DAS ORIENTAÇÕES
# =====================================================

def _normalize_text(text: str) -> str:
    """Normaliza texto para identificar repetições."""

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = text.casefold()

    text = re.sub(r"\s+", " ", text)

    return text.strip(" .!;")



def _unique_guidance(
    instructions: list[str],
) -> list[str]:
    """Remove orientações repetidas."""

    unique = []
    seen = set()

    for instruction in instructions:
        instruction = instruction.strip()

        if not instruction:
            continue

        normalized = _normalize_text(instruction)

        if normalized in seen:
            continue

        seen.add(normalized)
        unique.append(instruction)

    return unique


def _build_guidance(
    knowledge_base: dict[str, Any],
    fired_rule_ids: set[str],
    priority: str,
    insufficient: bool,
) -> list[str]:
    """Consolida encaminhamentos sem remover cuidados específicos."""

    guidance = []

    urgent = priority == "immediate"

    if urgent:
        guidance.append(
            "Solicite atendimento médico-veterinário imediato."
        )
    else:
        guidance.extend(
            knowledge_base.get("default_guidance", [])
        )

    # Frases equivalentes de encaminhamento.
    urgent_phrases = {
        "contate um medico-veterinario imediatamente",
        "contate um medico-veterinario em carater de emergencia",
        "contate o medico-veterinario imediatamente",
        "solicite atendimento medico-veterinario imediato",
    }

    for rule in knowledge_base["rules"]:

        if rule["id"] not in fired_rule_ids:
            continue

        instruction = rule.get("guidance", "").strip()

        if not instruction:
            continue

        if urgent:
            # Separa frases usando o ponto final.
            sentences = re.split(r"(?<=[.!?])\s+", instruction)

            filtered = []

            for sentence in sentences:
                normalized = _normalize_text(sentence)

                if normalized in urgent_phrases:
                    continue

                filtered.append(sentence.strip())

            instruction = " ".join(filtered).strip()

        if instruction:
            guidance.append(instruction)

    if insufficient:
        guidance.append(
            "Há informações desconhecidas. "
            "Complete-as somente quando for seguro, "
            "sem atrasar o atendimento veterinário."
        )

    return _unique_guidance(guidance)


# =====================================================
# MOTOR DE INFERÊNCIA
# =====================================================

def infer(
    facts: dict[str, Any],
    knowledge_base: dict[str, Any],
) -> InferenceResult:
    """Executa o encadeamento para frente.

    As regras são aplicadas até que nenhuma nova
    conclusão derivada seja produzida.
    """

    validate_knowledge_base(knowledge_base)

    if knowledge_base.get("questions"):
        question_ids = {
            question["id"]
            for question in knowledge_base["questions"]
        }
    else:
        question_ids = set(
            knowledge_base["fact_ids"]
        )

    # Mantém somente os fatos declarados.
    normalized = {
        key: value
        for key, value in facts.items()
        if key in question_ids
    }

    # Valores desconhecidos continuam desconhecidos.
    unknowns = sorted(
        key
        for key in question_ids
        if (
            key not in normalized
            or normalized[key] is None
        )
    )

    fired: list[dict[str, Any]] = []
    conclusions: list[dict[str, Any]] = []

    seen: set[str] = set()

    working_facts = dict(normalized)

    # =================================================
    # ENCADEAMENTO PARA FRENTE
    # =================================================

    changed = True

    while changed:
        changed = False

        for rule in knowledge_base["rules"]:

            if rule["id"] in seen:
                continue

            if not _matches(rule, working_facts):
                continue

            seen.add(rule["id"])

            fired.append({
                "id": rule["id"],
                "label": rule["label"],
                "because": rule["because"],
                "source_ids": rule.get(
                    "source_ids", []
                ),
            })

            conclusion = {
                "id": rule["conclusion"],
                "label": rule["conclusion_label"],
                "priority": rule["priority"],
                "rule_id": rule["id"],
            }

            conclusions.append(conclusion)

            # Uma regra pode derivar um novo fato,
            # permitindo o acionamento de outras regras.
            derived_fact = rule.get("derive")

            if (
                derived_fact
                and working_facts.get(derived_fact) is not True
            ):
                working_facts[derived_fact] = True
                changed = True

    # =================================================
    # PRIORIDADE
    # =================================================

    priorities = knowledge_base["priority_order"]

    if conclusions:
        priority = min(
            (
                item["priority"]
                for item in conclusions
            ),
            key=priorities.index,
        )
    else:
        priority = "none"

    # =================================================
    # VERIFICAÇÃO DE DADOS INSUFICIENTES
    # =================================================

    minimum_facts = knowledge_base.get(
        "required_for_clear_result", []
    )

    insufficient = any(
        key not in normalized
        or normalized[key] is None
        for key in minimum_facts
    )

    status = (
        "insufficient"
        if insufficient
        else "evaluated"
    )

    # =================================================
    # RESUMO
    # =================================================

    if conclusions:
        summary = knowledge_base[
            "priority_labels"
        ][priority]

    elif insufficient:
        summary = (
            "Informações insuficientes para verificar "
            "todos os sinais prioritários."
        )

    else:
        summary = (
            "Nenhum sinal de alerta coberto por esta "
            "versão das regras foi identificado."
        )

    # =================================================
    # ORIENTAÇÕES CONSOLIDADAS
    # =================================================

    guidance = _build_guidance(
        knowledge_base=knowledge_base,
        fired_rule_ids=seen,
        priority=priority,
        insufficient=insufficient,
    )

    # =================================================
    # RESULTADO EXPLICÁVEL
    # =================================================

    return InferenceResult(
        knowledge_base_version=knowledge_base["version"],
        priority=priority,
        status=status,
        summary=summary,
        conclusions=conclusions,
        fired_rules=fired,
        unknowns=unknowns,
        guidance=guidance,
        disclaimer=knowledge_base["disclaimer"],
    )
