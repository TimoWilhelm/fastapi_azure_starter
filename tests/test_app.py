import unittest

from fastapi import status

from tests._helper.client import setup_test_client


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = setup_test_client()

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
