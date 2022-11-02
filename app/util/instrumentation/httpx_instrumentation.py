import functools
import logging
import os
from typing import Awaitable, Callable, NamedTuple, cast

import httpx
from opencensus.trace import Span
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.blank_span import BlankSpan
from opencensus.trace.span import SpanKind
from opencensus.trace.tracer import Tracer

logger = logging.getLogger(__name__)

PID = COMMON_ATTRIBUTES["PID"]
HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_METHOD = COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_ROUTE = COMMON_ATTRIBUTES["HTTP_ROUTE"]
HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
ERROR_MESSAGE = COMMON_ATTRIBUTES["ERROR_MESSAGE"]
ERROR_NAME = COMMON_ATTRIBUTES["ERROR_NAME"]
STACKTRACE = COMMON_ATTRIBUTES["STACKTRACE"]

RequestHook = Callable[[Span | BlankSpan, "RequestInfo"], Awaitable[None]]
ResponseHook = Callable[
    [Span | BlankSpan, "RequestInfo", "ResponseInfo"], Awaitable[None]
]


class RequestInfo(NamedTuple):
    method: str
    url: httpx.URL
    headers: httpx.Headers | None
    stream: httpx.SyncByteStream | httpx.AsyncByteStream | None
    extensions: dict | None


class ResponseInfo(NamedTuple):
    status_code: int
    headers: httpx.Headers | None
    stream: httpx.SyncByteStream | httpx.AsyncByteStream | None
    extensions: dict | None


class AsyncOpenCensusTransport(httpx.AsyncBaseTransport):
    def __init__(
        self,
        tracer: Tracer,
        request_hook: RequestHook | None = None,
        response_hook: ResponseHook | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        """Async transport class that will trace all requests made with a client.


        Args:
            tracer (tracer_module.Tracer): The tracer to use for this transport.
            request_hook (RequestHook, optional):
                A hook that receives the span and request that is called
                right after the span is created. Defaults to None.
            response_hook (ResponseHook, optional):
                A hook that receives the span, request, and response
                that is called right before the span ends. Defaults to None.
            transport (httpx.AsyncBaseTransport, optional):
                The AsyncHTTPTransport instance to wrap. Defaults to AsyncHTTPTransport.
        """
        self._transport = transport or httpx.AsyncHTTPTransport()
        self._tracer = tracer
        self._request_hook = request_hook
        self._response_hook = response_hook

    async def handle_async_request(
        self, *args, **kwargs
    ) -> tuple[int, httpx.Headers, httpx.AsyncByteStream, dict] | httpx.Response:
        request: httpx.Request = args[0]

        method = request.method.upper()
        url = request.url
        headers = request.headers
        stream = request.stream
        extensions = request.extensions

        request_info = RequestInfo(method, url, headers, stream, extensions)

        with self._tracer.span(name=f"[{method}]{url}") as span:
            span.span_kind = SpanKind.CLIENT
            span.add_attribute(PID, str(os.getpid()))
            span.add_attribute(HTTP_METHOD, method)
            span.add_attribute(HTTP_URL, str(url))

            if self._request_hook is not None:
                await self._request_hook(span, request_info)

            try:
                tracer_headers = self._tracer.propagator.to_headers(
                    self._tracer.span_context
                )
                _headers = httpx.Headers(headers)
                _headers.update(tracer_headers)
                request.headers = _headers
            except Exception:  # pragma: NO COVER
                pass

            response = await self._transport.handle_async_request(*args, **kwargs)

            response: httpx.Response = response
            status_code = response.status_code
            headers = response.headers
            stream = response.stream
            extensions = response.extensions

            span.add_attribute(HTTP_STATUS_CODE, status_code)

            if self._response_hook is not None:
                await self._response_hook(
                    span,
                    request_info,
                    ResponseInfo(status_code, headers, stream, extensions),
                )

        return response


class _InstrumentedAsyncClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        tracer = kwargs.pop("tracer", None)

        if tracer is None:
            raise ValueError("Tracer is required")

        transport = kwargs.pop("transport", None)
        request_hook = kwargs.pop("request_hook", None)
        response_hook = kwargs.pop("response_hook", None)

        super().__init__(*args, **kwargs)

        self._original_transport: httpx.AsyncBaseTransport = self._transport
        self._transport = AsyncOpenCensusTransport(
            tracer=tracer,
            transport=transport,
            request_hook=request_hook,
            response_hook=response_hook,
        )

        self._is_instrumented = True


class HTTPXClientInstrumentation:
    def instrument_global(
        self,
        tracer: Tracer,
        request_hook: RequestHook | None = None,
        response_hook: ResponseHook | None = None,
    ):
        """Start global instrumentation for httpx.AsyncClient.

        Args:
            tracer (tracer_module.Tracer): The tracer to use for this transport.
            request_hook (RequestHook, optional):
                A hook that receives the span and request that is called
                right after the span is created. Defaults to None.
            response_hook (ResponseHook, optional):
                A hook that receives the span, request, and response
                that is called right before the span ends. Defaults to None.
        """
        self._original_async_client = httpx.AsyncClient

        instrumentedClient = functools.partial(
            _InstrumentedAsyncClient,
            tracer=tracer,
            request_hook=request_hook,
            response_hook=response_hook,
        )
        httpx.AsyncClient = instrumentedClient

    def stop_instrument_global(self):
        httpx.AsyncClient = self._original_async_client

    @staticmethod
    def instrument_client(
        client: httpx.AsyncClient,
        tracer: Tracer,
        request_hook: RequestHook | None = None,
        response_hook: ResponseHook | None = None,
    ) -> None:
        """Start instrumentation for an instance of httpx.AsyncClient.

        Args:
            client (httpx.AsyncClient): The httpx client.
            tracer (tracer_module.Tracer): The tracer to use for this transport.
            request_hook (RequestHook, optional):
                A hook that receives the span and request that is called
                right after the span is created. Defaults to None.
            response_hook (ResponseHook, optional):
                A hook that receives the span, request, and response
                that is called right before the span ends. Defaults to None.
        """
        if hasattr(client, "_is_instrumented"):
            logger.warning(
                "Attempting to instrument HTTPX client while already instrumented"
            )
            return

        instrumented_client = cast(_InstrumentedAsyncClient, client)

        instrumented_client._original_transport = client._transport
        instrumented_client._transport = AsyncOpenCensusTransport(
            tracer=tracer,
            transport=client._transport,
            request_hook=request_hook,
            response_hook=response_hook,
        )
        instrumented_client._is_instrumented = True

    @staticmethod
    def stop_instrument_client(
        client: httpx.AsyncClient,
    ) -> None:
        """Stop instrumentation for an instance of httpx.AsyncClient

        Args:
            client (httpx.AsyncClient): The httpx client.
        """
        if not hasattr(client, "_is_instrumented"):
            logger.warning(
                "Attempting to stop instrument HTTPX client while not instrumented"
            )
            return

        instrumented_client = cast(_InstrumentedAsyncClient, client)

        client._transport = instrumented_client._original_transport
        del instrumented_client._original_transport
        del instrumented_client._is_instrumented
