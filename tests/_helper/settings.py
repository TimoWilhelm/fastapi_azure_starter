from app.config import Settings

base_mock_settings = Settings(
    _env_file=None,
    TENANT_ID="00000000-0000-0000-0000-000000000000",
    OPENAPI_CLIENT_ID="00000000-0000-0000-0000-000000000000",
    API_CLIENT_ID="00000000-0000-0000-0000-000000000000",
    POSTGRES_CONNECTION_STRING="postgresql://user@example.com:5432/main",
)
