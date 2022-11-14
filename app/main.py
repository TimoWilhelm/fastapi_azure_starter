import logging

from fastapi import FastAPI, Request, Response, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.azure_scheme import AzureScheme
from app.config import get_settings
from app.limiter import RateLimit
from app.middleware import UncaughtExceptionHandlerMiddleware
from app.responses import default_responses
from app.telemetry.logging import UvicornLoggingFilter, init_logging

logger = logging.getLogger(__name__)

uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(UvicornLoggingFilter(path="/health", method="GET"))
uvicorn_access_logger.addFilter(UvicornLoggingFilter(path="/oauth2-redirect"))


settings = get_settings()

init_logging(settings.DEFAULT_LOG_LEVEL, settings.LOG_CONFIG)

app = FastAPI(
    title="Hello World",
    version="0.1.0",
    description="Hello World API",
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.OPENAPI_CLIENT_ID,
    },
)

FastAPIInstrumentor.instrument_app(app, excluded_urls="health,oauth2-redirect")


app.add_middleware(ProxyHeadersMiddleware)
app.add_middleware(UncaughtExceptionHandlerMiddleware)

AzureScheme.init(settings.TENANT_ID, settings.API_CLIENT_ID)

limiter = RateLimit.init(settings.REDIS_CONNECTION_STRING)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def load_auth_config() -> None:
    await AzureScheme.instance().load_config()


@app.get("/", include_in_schema=False)
async def get_root(request: Request, response: Response):
    return RedirectResponse("/docs")


@app.get("/health", include_in_schema=False)
def health(request: Request, response: Response):
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/error")
async def get_error(request: Request, response: Response):
    raise Exception("This is an error")


def add_routers():
    from app.routers import samples, users

    app.include_router(
        users.router,
        prefix="/users",
        tags=["users"],
        dependencies=[
            Security(AzureScheme.instance(), scopes=["user_impersonation"]),
        ],
        responses={**default_responses},
    )

    app.include_router(
        samples.router,
        prefix="/samples",
        tags=["samples"],
        dependencies=[
            Security(AzureScheme.instance(), scopes=["user_impersonation"]),
        ],
        responses={**default_responses},
    )


add_routers()
