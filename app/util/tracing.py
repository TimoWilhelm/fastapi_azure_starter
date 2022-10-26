from typing import Optional

from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.propagation import trace_context_http_header_format
from opencensus.trace.span_context import SpanContext
from opencensus.trace.samplers import Sampler

from opencensus.ext.azure.trace_exporter import AzureExporter

from app import settings

azure_trace_exporter = AzureExporter(
    connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING
)


def get_tracer(
    span_context: Optional[SpanContext] = None, sampler: Optional[Sampler] = None
):
    return Tracer(
        span_context=span_context,
        sampler=sampler or AlwaysOnSampler(),
        exporter=azure_trace_exporter,
        propagator=trace_context_http_header_format.TraceContextPropagator(),
    )
