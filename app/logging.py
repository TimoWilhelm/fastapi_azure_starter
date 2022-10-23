import os
import sys
import re
import logging
from typing import List, Optional

from opencensus.trace import config_integration
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.propagation import trace_context_http_header_format
from opencensus.trace.span_context import SpanContext
from opencensus.trace.samplers import Sampler

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter

from app import settings

_global_loggers = {}


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        arg_pattern = re.compile(r'%\((\w+)\)')
        arg_names = [x.group(1) for x in arg_pattern.finditer(self._fmt or '')]
        for field in arg_names:
            if field not in record.__dict__:
                record.__dict__[field] = None

        return super().format(record)


def init_logging():
    config_integration.trace_integrations(['logging', 'requests'])

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter(
        '[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s')
    )

    handlers: List[logging.Handler] = [
        console_handler,
        AzureLogHandler(
            connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING)
    ]

    logging.basicConfig(
        force=True,
        level=settings.LOG_LEVEL,
        handlers=handlers,
    )


def _get_key(pid: int, module_name: str):
    return f"{pid}:{module_name}"


# TODO: https://github.com/census-instrumentation/opencensus-python/pull/1158
# https://github.com/census-instrumentation/opencensus-python/issues/928#issuecomment-671489488
def get_logger(module_name: str):
    global _global_loggers

    key = _get_key(os.getpid(), module_name)

    existing_logger = _global_loggers.get(key)
    if existing_logger is not None:
        return existing_logger

    new_logger = logging.getLogger(module_name)

    _global_loggers[key] = new_logger
    return new_logger


def get_tracer(span_context: Optional[SpanContext] = None, sampler: Optional[Sampler] = None):
    return Tracer(
        span_context=span_context,
        sampler=sampler or AlwaysOnSampler(),
        exporter=AzureExporter(
            connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING),
        propagator=trace_context_http_header_format.TraceContextPropagator(),
    )
