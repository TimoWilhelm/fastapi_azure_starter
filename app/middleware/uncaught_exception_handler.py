import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class UncaughtExceptionHandlerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception:  # pragma: NO COVER
            logger.error("Uncaught exception", exc_info=True)

            return PlainTextResponse(
                content="Internal Server Error",
                status_code=500,
            )
