import sys
import logging

from uvicorn import run
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from fastapi import FastAPI, Security, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from pydantic import BaseModel

from app import settings, azure_scheme, limiter
from app.middleware import RequestTracingMiddleware
from app.routers import users
from app.responses import default_responses

logger = logging.getLogger(__name__)


def log_uncaught_exception(exc_type, exc_value, exc_traceback):
    if not issubclass(exc_type, KeyboardInterrupt):
        logger.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = log_uncaught_exception

app = FastAPI(
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.OPENAPI_CLIENT_ID,
    },
    title="Hello World",
    version="0.1.0",
    description="Hello World API",
)

app.add_middleware(ProxyHeadersMiddleware)

app.middleware("http")(
    RequestTracingMiddleware(
        app,
        excludelist_paths=["docs", "redoc", "openapi.json", "oauth2-redirect"],
    )
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


class Detail(BaseModel):
    detail: str


class Error(BaseModel):
    error: str


app.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
    responses={**default_responses},
)


@app.on_event("startup")
async def load_config() -> None:
    await azure_scheme.init()


@app.get("/", include_in_schema=False)
async def root(request: Request, response: Response):
    return RedirectResponse("/docs")


if __name__ == "__main__":
    run("main:app", reload=True, port=8080)
