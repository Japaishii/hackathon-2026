import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app

from app import database
from app.main import get_assessments, patch_follow_up, post_animal, post_assessment
from app.schemas import AnimalCreate, AssessmentCreate, FollowUpUpdate


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.original_db_path = database.DB_PATH
        self.temp = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self.temp.name) / "test.sqlite3"
        database.initialize()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
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

    def test_temperature_enum_accepts_not_measured(self):
        assessment = post_assessment(AssessmentCreate(answers={"fever_state":"not_measured"}))
        self.assertEqual(assessment["answers"]["fever_state"], "not_measured")
        self.assertNotIn("fever_state", assessment["result"]["unknowns"])

    def test_temperature_enum_rejects_undeclared_value(self):
        with self.assertRaises(HTTPException) as ctx:
            post_assessment(AssessmentCreate(answers={"fever_state":"maybe"}))
        self.assertEqual(ctx.exception.status_code, 422)


    def test_http_api_serves_home_questions_and_docs(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/").status_code, 200)
            self.assertEqual(client.get("/api/questions").status_code, 200)
            self.assertEqual(client.get("/docs").status_code, 200)

    def test_http_api_rejects_negative_onset_hours(self):
        with TestClient(app) as client:
            response = client.post("/api/assessments", json={"answers": {"onset_hours": -5}})
            self.assertEqual(response.status_code, 422)

    def test_http_api_accepts_nonnegative_onset_hours(self):
        with TestClient(app) as client:
            response = client.post("/api/assessments", json={"answers": {"onset_hours": 3}})
            self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main()
