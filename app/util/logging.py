import logging
import sys

from app import settings

from .otel import azure_monitor_handler

logger = logging.getLogger(__name__)


def init_logging():
    # messages lower than WARNING go to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(MaxLevelFilter(logging.WARNING))

    # messages >= WARNING ( and >= STDOUT_LOG_LEVEL ) go to stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)

    handlers: list[logging.Handler] = [
        stdout_handler,
        stderr_handler,
        azure_monitor_handler,
    ]

    for handler in handlers:
        handler.addFilter(DependenciesLoggingFilter())

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
    uvicorn_access_logger.handlers = handlers


class MaxLevelFilter(logging.Filter):
    """Filters out messages with level < LEVEL"""

    def __init__(self, level: int):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


class DependenciesLoggingFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.dependencies_log_level = logging._nameToLevel[
            settings.DEPENDENCIES_LOG_LEVEL
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        if (
            not record.name.startswith("app")
            and record.levelno < self.dependencies_log_level
        ):
            return False
        return True


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
