from typing import Union

from pydantic import AnyHttpUrl, BaseSettings, Field


class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: list[Union[str, AnyHttpUrl]] = [
        'http://localhost:8000']

    TENANT_ID: str = Field(..., env='TENANT_ID')
    OPENAPI_CLIENT_ID: str = Field(..., env='OPENAPI_CLIENT_ID')
    APP_CLIENT_ID: str = Field(..., env='APP_CLIENT_ID')

    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = Field(
        default='InstrumentationKey=00000000-0000-0000-0000-000000000000',
        env='APPLICATIONINSIGHTS_CONNECTION_STRING')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True


settings = Settings.parse_obj({})
