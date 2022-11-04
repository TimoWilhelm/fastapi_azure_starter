import logging
import re
import sys

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.trace import config_integration

from app import settings

logger = logging.getLogger(__name__)


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        arg_pattern = re.compile(r"%\((\w+)\)")
        arg_names = [x.group(1) for x in arg_pattern.finditer(self._fmt or "")]
        for field in arg_names:
            if field not in record.__dict__:
                record.__dict__[field] = None

        return super().format(record)


def init_logging():
    config_integration.trace_integrations(["logging"])

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        CustomFormatter("[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s")
    )

    handlers: list[logging.Handler] = [
        console_handler,
        AzureLogHandler(
            connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING
        ),
    ]

    logging.basicConfig(
        force=True,
        level=settings.LOG_LEVEL,
        handlers=handlers,
    )


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
