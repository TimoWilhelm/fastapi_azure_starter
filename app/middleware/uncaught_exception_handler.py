import logging

from starlette.types import ASGIApp

from fastapi import Request
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)


class UncaughtExceptionHandlerMiddleware:
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:  # pragma: NO COVER
            logger.error("Uncaught exception", exc_info=True)

            return PlainTextResponse(
                content="Internal Server Error",
                status_code=500,
            )
