import asyncio
import logging

from fastapi import FastAPI, Request, Response, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from uvicorn import run
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import azure_scheme, limiter, settings
from app.middleware import RequestTracingMiddleware, UncaughtExceptionHandlerMiddleware
from app.responses import default_responses
from app.routers import users
from app.util.instrumentation import HTTPXClientInstrumentation
from app.util.logging import UvicornLoggingFilter
from app.util.tracing import azure_trace_exporter, get_span, get_tracer

logger = logging.getLogger(__name__)

HTTPXClientInstrumentation().instrument_global(tracer=get_tracer())

uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(UvicornLoggingFilter(path="/health", method="GET"))
uvicorn_logger.addFilter(UvicornLoggingFilter(path="/oauth2-redirect"))

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
    excludelist_paths=[
        "/health",
        "/oauth2-redirect",
    ],
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


async def make_sample_request():
    async with AsyncClient() as client:
        result = await client.get("https://example.com")
        print(result.content)


@app.on_event("startup")
async def load_config() -> None:
    with get_span(name="app:startup"):
        try:
            await asyncio.gather(
                azure_scheme.init(),
                make_sample_request(),
            )
        except Exception:  # pragma: NO COVER
            logger.error("Error during application startup", exc_info=True)
            raise


@app.get("/", include_in_schema=False)
async def get_root(request: Request, response: Response):
    return RedirectResponse("/docs")


@app.get("/health", include_in_schema=False)
def health(request: Request, response: Response):
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/error")
async def get_error(request: Request, response: Response):
    raise Exception("This is an error")


if __name__ == "__main__":
    run("main:app", reload=True, port=8000)
