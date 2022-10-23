from typing import Union

from pydantic import AnyHttpUrl, BaseSettings, Field


class Settings(BaseSettings):
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    SECRET_KEY: str = Field(default='', env='SECRET_KEY')
    BACKEND_CORS_ORIGINS: list[Union[str, AnyHttpUrl]] = [
        'http://localhost:8000']
    OPENAPI_CLIENT_ID: str = Field(default='', env='OPENAPI_CLIENT_ID')
    APP_CLIENT_ID: str = Field(default='', env='APP_CLIENT_ID')
    TENANT_ID: str = Field(default='', env='TENANT_ID')
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = Field(
        default='InstrumentationKey=00000000-0000-0000-0000-000000000000',
        env='APPLICATIONINSIGHTS_CONNECTION_STRING')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True


settings = Settings()
