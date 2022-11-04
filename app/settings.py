import multiprocessing

from pydantic import AnyHttpUrl, BaseSettings, Field


class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = ["http://localhost:8000"]

    TENANT_ID: str = Field(..., env="TENANT_ID")
    OPENAPI_CLIENT_ID: str = Field(..., env="OPENAPI_CLIENT_ID")
    API_CLIENT_ID: str = Field(..., env="API_CLIENT_ID")

    REDIS_CONNECTION_STRING: str | None = Field(env="REDIS_CONNECTION_STRING")

    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # https://docs.gunicorn.org/en/stable/design.html#how-many-workers
    WORKER_COUNT: int = Field(
        default=multiprocessing.cpu_count() * 2 + 1,
        env="WORKER_COUNT",
    )

    APPLICATIONINSIGHTS_CONNECTION_STRING: str = Field(
        default="InstrumentationKey=00000000-0000-0000-0000-000000000000",
        env="APPLICATIONINSIGHTS_CONNECTION_STRING",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()  # pyright: ignore[reportGeneralTypeIssues]
