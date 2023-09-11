import unittest

from fastapi import status

from tests._helper.client import setup_test_client


class TestUsers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = setup_test_client()

    def test_greet(self):
        # Act
        response = self.client.get("/users/greet")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"greeting": "Hello Mock User!"})
