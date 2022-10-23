from typing import List, Optional
from fastapi import Request

from starlette.types import ASGIApp

from opencensus.trace import (
    attributes_helper,
    execution_context,
)
from opencensus.trace.span import SpanKind
from opencensus.trace.utils import disable_tracing_url
from opencensus.trace.propagation import trace_context_http_header_format

from app.logging import get_logger, get_tracer

HTTP_HOST = attributes_helper.COMMON_ATTRIBUTES["HTTP_HOST"]
HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES["HTTP_ROUTE"]
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]


class RequestTracingMiddleware:

    def __init__(
        self,
        app: ASGIApp,
        excludelist_paths: Optional[List[str]] = None,
        excludelist_hostnames: Optional[List[str]] = None,
    ) -> None:
        self.app = app
        self.excludelist_paths = excludelist_paths
        self.excludelist_hostnames = excludelist_hostnames
        self.propagator = trace_context_http_header_format.TraceContextPropagator()

    async def __call__(self, request: Request, call_next):

        # Do not trace if the url is in the exclude list
        if disable_tracing_url(str(request.url), self.excludelist_paths):
            return await call_next(request)

        logger = get_logger(__name__)

        span_context = self.propagator.from_headers(request.headers)
        tracer = get_tracer(span_context=span_context)

        try:

            span = tracer.start_span()
            span.span_kind = SpanKind.SERVER
            span.name = "[{}]{}".format(request.method, request.url)
            tracer.add_attribute_to_current_span(
                HTTP_HOST, request.url.hostname)
            tracer.add_attribute_to_current_span(HTTP_METHOD, request.method)
            tracer.add_attribute_to_current_span(HTTP_PATH, request.url.path)
            tracer.add_attribute_to_current_span(HTTP_URL, str(request.url))
            execution_context.set_opencensus_attr(
                "excludelist_hostnames", self.excludelist_hostnames
            )
        except Exception:  # pragma: NO COVER
            logger.error("Failed to trace request", exc_info=True)

        response = await call_next(request)
        try:
            tracer.add_attribute_to_current_span(
                HTTP_STATUS_CODE, response.status_code)
        except Exception:  # pragma: NO COVER
            logger.error("Failed to trace response", exc_info=True)
        finally:
            tracer.end_span()
            return response
