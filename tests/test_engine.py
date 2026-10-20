import json
import unittest
from pathlib import Path

from app.specialist.engine import KnowledgeBaseError, infer, load_knowledge_base, validate_knowledge_base


ROOT = Path(__file__).resolve().parents[1]
KB = load_knowledge_base(ROOT / "knowledge" / "rules.json")


class EngineTests(unittest.TestCase):
    def blank_answers(self):
        return {q["id"]: None for q in json.loads((ROOT / "knowledge" / "questions.json").read_text(encoding="utf-8"))["questions"]}

    def test_emergency_rule_and_explanation_are_deterministic(self):
        facts = self.blank_answers()
        facts.update(respiratory_distress=True, sudden_left_abdominal_distension=True)
        first = infer(facts, KB).to_dict()
        second = infer(facts, KB).to_dict()
        self.assertEqual(first, second)
        self.assertEqual(first["priority"], "immediate")
        self.assertIn("R-RESP-001", [r["id"] for r in first["fired_rules"]])
        self.assertIn("R-BLOAT-001", [r["id"] for r in first["fired_rules"]])

    def test_unknown_is_not_treated_as_negative(self):
        result = infer({"respiratory_distress": None}, KB)
        self.assertEqual(result.status, "insufficient")
        self.assertIn("respiratory_distress", result.unknowns)
        self.assertFalse(result.fired_rules)

    def test_mammary_signs_and_systemic_sign_are_explained(self):
        facts = self.blank_answers()
        facts.update(abnormal_milk=True, fever=True)
        result = infer(facts, KB)
        ids = [r["id"] for r in result.fired_rules]
        self.assertEqual(result.priority, "immediate")
        self.assertIn("R-UDDER-001", ids)
        self.assertIn("R-UDDER-SYSTEMIC-001", ids)

    def test_complete_negative_screen_does_not_claim_animal_is_healthy(self):
        facts = {q["id"]: False for q in json.loads((ROOT / "knowledge" / "questions.json").read_text(encoding="utf-8"))["questions"] if q["type"] == "boolean"}
        result = infer(facts, KB)
        self.assertEqual(result.status, "evaluated")
        self.assertEqual(result.priority, "none")
        self.assertIn("Nenhum sinal de alerta coberto", result.summary)

    def test_duplicate_rule_id_is_rejected(self):
        bad = dict(KB)
        bad["rules"] = KB["rules"] + [dict(KB["rules"][0])]
        with self.assertRaises(KnowledgeBaseError):
            validate_knowledge_base(bad)


if __name__ == "__main__":
    unittest.main()
