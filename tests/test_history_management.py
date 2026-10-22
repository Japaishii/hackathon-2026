import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app
from app import database


class HistoryManagementTests(unittest.TestCase):
    def setUp(self):
        self.old_path = database.DB_PATH
        self.temp = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self.temp.name) / 'test.sqlite3'
        database.initialize()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        database.DB_PATH = self.old_path
        self.temp.cleanup()

    def test_paginated_history_and_delete(self):
        ids = []
        for _ in range(7):
            response = self.client.post('/api/assessments', json={'answers': {}})
            self.assertEqual(response.status_code, 201)
            ids.append(response.json()['id'])
        first = self.client.get('/api/assessments/page?page=1&page_size=5').json()
        second = self.client.get('/api/assessments/page?page=2&page_size=5').json()
        self.assertEqual(first['total'], 7)
        self.assertEqual(len(first['items']), 5)
        self.assertEqual(len(second['items']), 2)
        self.assertEqual(first['items'][0]['id'], ids[-1])
        target = ids[-1]
        self.assertEqual(self.client.patch(f'/api/assessments/{target}/follow-up', json={'follow_up':'Contato realizado'}).status_code, 200)
        self.assertEqual(self.client.delete(f'/api/assessments/{target}').status_code, 204)
        self.assertEqual(self.client.get(f'/api/assessments/{target}').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/assessments/{target}').status_code, 404)
        self.assertEqual(self.client.get('/api/assessments/page').json()['total'], 6)

    def test_invalid_pagination(self):
        for query in ('page=0', 'page_size=0', 'page_size=51'):
            self.assertEqual(self.client.get('/api/assessments/page?' + query).status_code, 422)
