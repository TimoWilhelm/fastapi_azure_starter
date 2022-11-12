import unittest
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.database.tables.sample_table import SampleTable
from app.repositories.sample_repository import SampleRepository, get_sample_repository
from tests._helper.security import MockSecurity
from tests._helper.settings import base_mock_settings


class TestSamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("app.config.get_settings", return_value=base_mock_settings), patch(
            "app.azure_scheme.get_azure_scheme", return_value=MockSecurity
        ):
            from app.main import app

            cls.mock_sample_repository = AsyncMock(SampleRepository)
            app.dependency_overrides = {
                get_sample_repository: lambda: cls.mock_sample_repository,
            }
            cls.client = TestClient(app)

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
