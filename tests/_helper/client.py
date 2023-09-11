from typing import Any, Callable
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests._helper.security import MockSecurity
from tests._helper.settings import base_mock_settings


def setup_test_client(
    dependency_overrides: dict[Callable[..., Any], Callable[..., Any]] = {}
):
    with patch("app.config.get_settings", return_value=base_mock_settings), patch(
        "app.azure_scheme.AzureScheme",
        MockSecurity,
    ):
        from app.main import app

        app.dependency_overrides = dependency_overrides
        return TestClient(app)
