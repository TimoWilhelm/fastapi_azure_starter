import logging

from uvicorn import run
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from fastapi import FastAPI, Security, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import settings, azure_scheme, limiter
from app.middleware import UncaughtExceptionHandlerMiddleware, RequestTracingMiddleware
from app.routers import users
from app.responses import default_responses
from app.util.tracing import azure_trace_exporter

logger = logging.getLogger(__name__)

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

app.add_middleware(ProxyHeadersMiddleware)
app.add_middleware(UncaughtExceptionHandlerMiddleware)
app.add_middleware(
    RequestTracingMiddleware,
    excludelist_paths=["docs", "redoc", "openapi.json", "oauth2-redirect"],
    exporter=azure_trace_exporter,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
    responses={**default_responses},
)


@app.on_event("startup")
async def load_config() -> None:
    try:
        await azure_scheme.init()
    except Exception:  # pragma: NO COVER
        logger.error("Error during application startup", exc_info=True)
        raise


@app.get("/", include_in_schema=False)
async def root(request: Request, response: Response):
    return RedirectResponse("/docs")


@app.get("/error")
async def error(request: Request, response: Response):
    raise Exception("This is an error")


if __name__ == "__main__":
    run("main:app", reload=True, port=8000)
