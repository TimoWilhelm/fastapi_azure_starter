import logging
import sys

from app.telemetry.azure_monitor import AzureMonitor

logger = logging.getLogger(__name__)


def init_logging(default_level=logging.INFO, log_config: dict[str, str] = None):
    # messages < WARNING go to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(MaxLevelFilter(logging.WARNING))

    # messages >= WARNING go to stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)

    handlers: list[logging.Handler] = [
        stdout_handler,
        stderr_handler,
        AzureMonitor.azure_monitor_log_handler,
    ]

    logging.basicConfig(
        force=True,
        level=default_level,
        handlers=handlers,
        format="[%(levelname)s] [%(asctime)s] [%(process)d] [%(name)s] %(message)s",
    )

    if log_config is not None:
        for key, value in log_config.items():
            logging.getLogger(key).setLevel(value)

    # since uvicorn logging is configured before this function is called,
    # we need to overwrite the handlers.
    logging.getLogger("uvicorn").handlers = handlers
    logging.getLogger("uvicorn.access").handlers = handlers


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
