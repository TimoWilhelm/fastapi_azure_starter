import unittest

from fastapi.testclient import TestClient

from app.main import app


class TestClient(unittest.TestCase):
    client = TestClient(app)

    def test_client(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
