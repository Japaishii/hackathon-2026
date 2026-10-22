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
        facts.update(abnormal_milk=True, fever_state="fever_present")
        result = infer(facts, KB)
        ids = [r["id"] for r in result.fired_rules]
        self.assertEqual(result.priority, "immediate")
        self.assertIn("R-UDDER-001", ids)
        self.assertIn("R-UDDER-SYSTEMIC-001", ids)

    def test_sudden_distension_alone_triggers_immediate_bloat_alert(self):
        facts = self.blank_answers()
        facts.update(sudden_left_abdominal_distension=True, respiratory_distress=False)
        result = infer(facts, KB)
        ids = [rule["id"] for rule in result.fired_rules]
        self.assertEqual(result.priority, "immediate")
        self.assertIn("R-BLOAT-001", ids)
        self.assertNotIn("R-RESP-001", ids)

    def test_udder_inflammation_and_systemic_sign_trigger_urgent_rule(self):
        facts = self.blank_answers()
        facts.update(udder_inflammation=True, abnormal_milk=False, fever_state="fever_present")
        result = infer(facts, KB)
        ids = [rule["id"] for rule in result.fired_rules]
        self.assertEqual(result.priority, "immediate")
        self.assertIn("R-UDDER-001", ids)
        self.assertIn("R-UDDER-SYSTEMIC-001", ids)

    def test_udder_inflammation_and_reduced_appetite_trigger_urgent_rule(self):
        facts = self.blank_answers()
        facts.update(udder_inflammation=True, abnormal_milk=False, reduced_appetite=True)
        result = infer(facts, KB)
        self.assertEqual(result.priority, "immediate")
        self.assertIn("R-UDDER-SYSTEMIC-001", [rule["id"] for rule in result.fired_rules])

    def test_not_measured_temperature_is_not_treated_as_fever_or_unknown(self):
        facts = self.blank_answers()
        facts.update(
            respiratory_distress=False, unable_to_rise=False,
            sudden_left_abdominal_distension=False, abnormal_milk=True,
            udder_inflammation=False, fever_state="not_measured",
            reduced_appetite=False,
        )
        result = infer(facts, KB)
        ids = [rule["id"] for rule in result.fired_rules]
        self.assertEqual(result.priority, "veterinary_assessment")
        self.assertIn("R-UDDER-001", ids)
        self.assertNotIn("R-UDDER-SYSTEMIC-001", ids)
        self.assertNotIn("fever_state", result.unknowns)

    def test_reduced_appetite_and_milk_drop_trigger_veterinary_assessment(self):
        facts = self.blank_answers()
        facts.update(reduced_appetite=True, milk_drop=True)
        result = infer(facts, KB)
        self.assertEqual(result.priority, "veterinary_assessment")
        self.assertIn("R-METABOLIC-SYSTEMIC-001", [rule["id"] for rule in result.fired_rules])

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
