import multiprocessing
from functools import cache
from typing import Literal

from pydantic import (
    AnyHttpUrl,
    BaseConfig,
    BaseSettings,
    Field,
    PostgresDsn,
    RedisDsn,
    condecimal,
    conint,
    constr,
)

LOG_LEVELS = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    class Config(BaseConfig):
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = True
        allow_mutation = False

    ENVIRONMENT: Literal["DEVELOPMENT", "STAGING", "PRODUCTION"] = Field(
        default="DEVELOPMENT", env="ENVIRONMENT"
    )

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = Field(
        default=["http://localhost:8000"], env="BACKEND_CORS_ORIGINS"
    )

    TENANT_ID: constr(strip_whitespace=True) = Field(..., env="TENANT_ID")
    OPENAPI_CLIENT_ID: constr(strip_whitespace=True) = Field(
        ..., env="OPENAPI_CLIENT_ID"
    )
    API_CLIENT_ID: constr(strip_whitespace=True) = Field(..., env="API_CLIENT_ID")

    POSTGRES_CONNECTION_STRING: PostgresDsn = Field(
        ..., env="POSTGRES_CONNECTION_STRING"
    )
    REDIS_CONNECTION_STRING: RedisDsn | None = Field(env="REDIS_CONNECTION_STRING")

    GUNICORN_LOG_LEVEL: LOG_LEVELS = Field(default="INFO", env="GUNICORN_LOG_LEVEL")
    DEFAULT_LOG_LEVEL: LOG_LEVELS = Field(default="WARNING", env="DEFAULT_LOG_LEVEL")
    LOG_CONFIG: dict[str, LOG_LEVELS] = Field(
        default={
            "app": "INFO",
            "uvicorn.access": "INFO",
            "uvicorn.error": "INFO",
            "sqlalchemy.engine": "WARNING",
            "sqlalchemy.pool": "WARNING",
            "sqlalchemy.orm": "WARNING",
        },
        env="LOG_CONFIG",
    )

    # https://docs.gunicorn.org/en/stable/design.html#how-many-workers
    WORKER_COUNT: conint(gt=0, le=multiprocessing.cpu_count() * 2 + 1) = Field(
        default=multiprocessing.cpu_count() * 2 + 1,
        env="WORKER_COUNT",
    )

    APPLICATIONINSIGHTS_CONNECTION_STRING: constr(strip_whitespace=True) | None = Field(
        env="APPLICATIONINSIGHTS_CONNECTION_STRING",
    )

    TRACING_SAMPLER_RATE: condecimal(ge=0.0, le=1.0, decimal_places=5) = Field(
        default=1.0,
        env="TRACING_SAMPLER_RATE",
    )

    SYSTEM_METRICS_ENABLED: bool = Field(
        default=False,
        env="SYSTEM_METRICS_ENABLED",
    )


@cache
def get_settings():
    return Settings()
