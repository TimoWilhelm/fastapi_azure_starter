from uvicorn import run
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from fastapi import FastAPI, Security, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from opencensus.trace import samplers
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import settings, azure_scheme, limiter
from app.middleware import TracerMiddleware
from app.routers import users


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


app.include_router(users.router, prefix="/users", tags=["users"], dependencies=[
                   Security(azure_scheme, scopes=['user_impersonation'])])


@app.on_event('startup')
async def load_config() -> None:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()


@app.get("/", include_in_schema=False)
async def root(request: Request, response: Response):
    return RedirectResponse("/docs")


if __name__ == '__main__':
    run('main:app', reload=True)
