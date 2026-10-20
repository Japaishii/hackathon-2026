import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

from app import database
from app.main import get_assessments, patch_follow_up, post_animal, post_assessment
from app.schemas import AnimalCreate, AssessmentCreate, FollowUpUpdate


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self.temp.name) / "test.sqlite3"
        database.initialize()

    def tearDown(self):
        self.temp.cleanup()

    def test_animal_assessment_history_and_follow_up(self):
        animal = post_animal(AnimalCreate(identifier="V-101", breed="Holandesa"))
        answers = {"respiratory_distress": True, "unable_to_rise": False, "sudden_left_abdominal_distension": True, "abnormal_milk": False, "udder_inflammation": False}
        assessment = post_assessment(AssessmentCreate(animal_id=animal["id"], answers=answers))
        self.assertEqual(assessment["result"]["priority"], "immediate")
        history = get_assessments(animal_id=animal["id"])
        self.assertEqual(len(history), 1)
        updated = patch_follow_up(assessment["id"], FollowUpUpdate(follow_up="Veterinário contatado"))
        self.assertEqual(updated["follow_up"], "Veterinário contatado")

    def test_invalid_answer_type_is_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            post_assessment(AssessmentCreate(answers={"respiratory_distress":"yes"}))
        self.assertEqual(ctx.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
