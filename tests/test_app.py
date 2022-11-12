import unittest
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from tests._helper.security import MockSecurity
from tests._helper.settings import base_mock_settings


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("app.config.get_settings", return_value=base_mock_settings), patch(
            "app.azure_scheme.get_azure_scheme", return_value=MockSecurity
        ):
            from app.main import app

            cls.client = TestClient(app)

    def test_get_root(self):
        response = self.client.get("/", allow_redirects=False)
        self.assertEqual(response.status_code, status.HTTP_307_TEMPORARY_REDIRECT)
        self.assertEqual(response.headers["Location"], "/docs")

    def test_get_docs(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
