import logging
import sys

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.trace import config_integration

from app import settings

logger = logging.getLogger(__name__)


def init_logging():
    config_integration.trace_integrations(["logging"])

    # messages lower than WARNING go to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(MaxLevelFilter(logging.WARNING))

    # messages >= WARNING ( and >= STDOUT_LOG_LEVEL ) go to stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)

    handlers: list[logging.Handler] = [
        stdout_handler,
        stderr_handler,
        AzureLogHandler(
            connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING
        ),
    ]

    logging.basicConfig(
        force=True,
        level=settings.LOG_LEVEL,
        handlers=handlers,
        format="[%(levelname)s] [%(asctime)s] [%(process)d] %(message)s",
    )

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.setLevel(settings.LOG_LEVEL)
    uvicorn_error_logger.handlers = handlers

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(settings.LOG_LEVEL)
    uvicorn_error_logger.handlers = handlers


class MaxLevelFilter(logging.Filter):
    """Filters out messages with level < LEVEL"""

    def __init__(self, level: int):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


class UvicornLoggingFilter(logging.Filter):
    def __init__(self, path: str, method: str | None = None):
        """Filter out uvicorn log records for a specific endpoint.
        Usage:
            uvicorn_logger = logging.getLogger("uvicorn.access")
            uvicorn_logger.addFilter(UvicornLoggingFilter(path="/health", method="GET"))
        Args:
            path (str): The request path to filter.
            method (str, optional): The request method to filter. Defaults to None.
        """
        super().__init__()
        self._path = path
        self._method = method

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args is None or len(record.args) < 3:
            return True

        # Record args are (remote_addr, method, path_with_query, http_version, status_code)
        method: str = record.args[1]  # type: ignore
        path_with_query: str = record.args[2]  # type: ignore

        if self._method is not None and method != self._method:
            return True

        path = path_with_query.split("?")[0].rstrip("/")

        if path == self._path:
            return False

        return True
