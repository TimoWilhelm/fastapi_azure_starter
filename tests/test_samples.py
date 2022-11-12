import unittest
from unittest.mock import AsyncMock

from fastapi import status

from app.database.tables.sample_table import SampleTable
from app.repositories.sample_repository import SampleRepository, get_sample_repository
from tests._helper.client import setup_test_client


class TestSamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_sample_repository = AsyncMock(SampleRepository)
        cls.client = setup_test_client(
            {
                get_sample_repository: lambda: cls.mock_sample_repository,
            }
        )

    def tearDown(self):
        self.mock_sample_repository.reset_mock()

    def test_get_samples(self):
        # Arrange
        self.mock_sample_repository.get.return_value = [
            SampleTable(id=1, name="test1"),
        ]

        # Act
        response = self.client.get("/samples")

        # Assert
        self.mock_sample_repository.get.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(), [{"id": 1, "name": "test1", "description": None}]
        )

    def test_get_sample_by_id(self):
        # Arrange
        self.mock_sample_repository.get_by_id.return_value = SampleTable(
            id=1, name="test1"
        )

        # Act
        response = self.client.get("/samples/1")

        # Assert
        self.mock_sample_repository.get_by_id.assert_called_once_with(1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(), {"id": 1, "name": "test1", "description": None}
        )
