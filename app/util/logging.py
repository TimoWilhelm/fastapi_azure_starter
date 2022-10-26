import sys
import re
import logging

from typing import List

from opencensus.trace import config_integration

from opencensus.ext.azure.log_exporter import AzureLogHandler

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

    handlers: List[logging.Handler] = [
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
