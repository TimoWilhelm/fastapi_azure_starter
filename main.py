from typing import Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, Field

import uvicorn
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from fastapi import FastAPI, Security, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from fastapi_azure_auth.user import User

from tracer_middleware import TracerMiddleware

from opencensus.trace import samplers
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


class Settings(BaseSettings):
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

app = FastAPI(
    swagger_ui_oauth2_redirect_url='/oauth2-redirect',
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': settings.OPENAPI_CLIENT_ID,
    },
)

app.add_middleware(ProxyHeadersMiddleware)

azure_log_handler = AzureLogHandler(
    connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING)
azure_trace_exporter = AzureExporter(
    connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING)

app.middleware("http")(TracerMiddleware(
    app,
    excludelist_paths=['/docs', '/redoc', '/oauth2-redirect'],
    sampler=samplers.AlwaysOnSampler(),
    log_handler=azure_log_handler,
    trace_exporter=azure_trace_exporter))


def key_func(request: Request) -> str:
    user: Optional[User] = request.state.user
    if user is not None:
        return str(user.claims.get('sub'))

    if (request.client is not None):
        return request.client.host

    return "default"


limiter = Limiter(
    key_func=key_func,
    default_limits=["100/minute"],
    headers_enabled=True,
    storage_uri="memory://",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin)
                       for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes={
        f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user_impersonation',
    }
)


@app.on_event('startup')
async def load_config() -> None:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()


@app.get("/", dependencies=[Security(azure_scheme)])
@limiter.limit("5/minute")
async def hello_user(request: Request, response: Response):
    user: User = request.state.user
    return {"message": f"Hello {user.name}!"}


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
