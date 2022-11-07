import multiprocessing
from typing import Literal

from pydantic import AnyHttpUrl, BaseSettings, Field, RedisDsn


class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = Field(
        default=["http://localhost:8000"], env="BACKEND_CORS_ORIGINS"
    )

    TENANT_ID: str = Field(..., env="TENANT_ID")
    OPENAPI_CLIENT_ID: str = Field(..., env="OPENAPI_CLIENT_ID")
    API_CLIENT_ID: str = Field(..., env="API_CLIENT_ID")

    REDIS_CONNECTION_STRING: RedisDsn | None = Field(env="REDIS_CONNECTION_STRING")

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", env="LOG_LEVEL"
    )
    DEPENDENCIES_LOG_LEVEL: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = Field(
        default="WARNING",
        env="DEPENDENCIES_LOG_LEVEL",
    )

    # https://docs.gunicorn.org/en/stable/design.html#how-many-workers
    WORKER_COUNT: int = Field(
        default=multiprocessing.cpu_count() * 2 + 1,
        env="WORKER_COUNT",
        gt=0,
        le=multiprocessing.cpu_count() * 2 + 1,
    )

    APPLICATIONINSIGHTS_CONNECTION_STRING: str = Field(
        default="InstrumentationKey=00000000-0000-0000-0000-000000000000",
        env="APPLICATIONINSIGHTS_CONNECTION_STRING",
    )

    TRACING_SAMPLER_RATE: float = Field(
        default=1.0,
        env="TRACING_SAMPLER_RATE",
        ge=0.0,
        le=1.0,
    )

    SYSTEM_METRICS_ENABLED: bool = Field(
        default=False,
        env="SYSTEM_METRICS_ENABLED",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()  # pyright: ignore[reportGeneralTypeIssues]
