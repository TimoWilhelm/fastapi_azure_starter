import functools
import logging
import typing

import httpx
from opencensus.trace import Span, attributes_helper
from opencensus.trace import span as span_module
from opencensus.trace import tracer as tracer_module
from opencensus.trace.blank_span import BlankSpan

logger = logging.getLogger(__name__)

HTTP_URL = attributes_helper.COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES["HTTP_ROUTE"]
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
ERROR_MESSAGE = attributes_helper.COMMON_ATTRIBUTES["ERROR_MESSAGE"]
ERROR_NAME = attributes_helper.COMMON_ATTRIBUTES["ERROR_NAME"]
STACKTRACE = attributes_helper.COMMON_ATTRIBUTES["STACKTRACE"]

RequestHook = typing.Callable[[Span | BlankSpan, "RequestInfo"], typing.Awaitable[None]]
ResponseHook = typing.Callable[
    [Span | BlankSpan, "RequestInfo", "ResponseInfo"], typing.Awaitable[None]
]


class RequestInfo(typing.NamedTuple):
    method: str
    url: httpx.URL
    headers: typing.Optional[httpx.Headers]
    stream: typing.Optional[typing.Union[httpx.SyncByteStream, httpx.AsyncByteStream]]
    extensions: typing.Optional[dict]


class ResponseInfo(typing.NamedTuple):
    status_code: int
    headers: typing.Optional[httpx.Headers]
    stream: typing.Optional[typing.Union[httpx.SyncByteStream, httpx.AsyncByteStream]]
    extensions: typing.Optional[dict]


class AsyncOpenCensusTransport(httpx.AsyncBaseTransport):
    def __init__(
        self,
        tracer: tracer_module.Tracer,
        request_hook: typing.Optional[RequestHook] = None,
        response_hook: typing.Optional[ResponseHook] = None,
        transport: typing.Optional[httpx.AsyncBaseTransport] = None,
    ):
        """Async transport class that will trace all requests made with a client.


        Args:
            tracer (tracer_module.Tracer): The tracer to use for this transport.
            request_hook (typing.Optional[RequestHook], optional):
                A hook that receives the span and request that is called
                right after the span is created. Defaults to None.
            response_hook (typing.Optional[ResponseHook], optional):
                A hook that receives the span, request, and response
                that is called right before the span ends. Defaults to None.
            transport (typing.Optional[httpx.AsyncBaseTransport], optional):
                The AsyncHTTPTransport instance to wrap. Defaults to AsyncHTTPTransport.
        """
        self._transport = transport or httpx.AsyncHTTPTransport()
        self._tracer = tracer
        self._request_hook = request_hook
        self._response_hook = response_hook

    async def handle_async_request(
        self, *args, **kwargs
    ) -> typing.Union[
        typing.Tuple[int, httpx.Headers, httpx.AsyncByteStream, dict],
        httpx.Response,
    ]:
        request: httpx.Request = args[0]

        method = request.method.upper()
        url = request.url
        headers = request.headers
        stream = request.stream
        extensions = request.extensions

        request_info = RequestInfo(method, url, headers, stream, extensions)

        with self._tracer.span(name=f"[{method}]{url}") as span:
            span.span_kind = span_module.SpanKind.CLIENT

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
        tracer: tracer_module.Tracer,
        request_hook: typing.Optional[RequestHook] = None,
        response_hook: typing.Optional[ResponseHook] = None,
    ):
        """Start global instrumentation for httpx.AsyncClient.

        Args:
            tracer (tracer_module.Tracer): The tracer to use for this transport.
            request_hook (typing.Optional[RequestHook], optional):
                A hook that receives the span and request that is called
                right after the span is created. Defaults to None.
            response_hook (typing.Optional[ResponseHook], optional):
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
        tracer: tracer_module.Tracer,
        request_hook: typing.Optional[RequestHook] = None,
        response_hook: typing.Optional[ResponseHook] = None,
    ) -> None:
        """Start instrumentation for an instance of httpx.AsyncClient.

        Args:
            client (httpx.AsyncClient): The httpx client.
            tracer (tracer_module.Tracer): The tracer to use for this transport.
            request_hook (typing.Optional[RequestHook], optional):
                A hook that receives the span and request that is called
                right after the span is created. Defaults to None.
            response_hook (typing.Optional[ResponseHook], optional):
                A hook that receives the span, request, and response
                that is called right before the span ends. Defaults to None.
        """
        if hasattr(client, "_is_instrumented"):
            logger.warning(
                "Attempting to instrument HTTPX client while already instrumented"
            )
            return

        instrumented_client = typing.cast(_InstrumentedAsyncClient, client)

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

        instrumented_client = typing.cast(_InstrumentedAsyncClient, client)

        client._transport = instrumented_client._original_transport
        del instrumented_client._original_transport
        del instrumented_client._is_instrumented
