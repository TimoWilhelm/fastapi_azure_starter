import logging

from fastapi import FastAPI, Request, Response, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import azure_scheme, limiter, settings
from app.middleware import UncaughtExceptionHandlerMiddleware
from app.responses import default_responses
from app.routers import users
from app.util.logging import UvicornLoggingFilter

logger = logging.getLogger(__name__)

uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(UvicornLoggingFilter(path="/health", method="GET"))
uvicorn_access_logger.addFilter(UvicornLoggingFilter(path="/oauth2-redirect"))

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
async def init_auth() -> None:
    await azure_scheme.init()


@app.get("/", include_in_schema=False)
async def get_root(request: Request, response: Response):
    return RedirectResponse("/docs")


@app.get("/health", include_in_schema=False)
def health(request: Request, response: Response):
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/error")
async def get_error(request: Request, response: Response):
    raise Exception("This is an error")
