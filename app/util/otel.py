from azure.monitor.opentelemetry.exporter import (
    AzureMonitorLogExporter,
    AzureMonitorMetricExporter,
    AzureMonitorTraceExporter,
)
from opentelemetry import metrics, trace
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler, set_logger_provider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics._internal import MeterProvider
from opentelemetry.sdk.metrics._internal.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from app import settings

# trace
trace_exporter = AzureMonitorTraceExporter.from_connection_string(
    settings.APPLICATIONINSIGHTS_CONNECTION_STRING
)

_trace_provider = TracerProvider(
    sampler=TraceIdRatioBased(settings.TRACING_SAMPLER_RATE)
)
_trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))


# metric
metric_exporter = AzureMonitorMetricExporter.from_connection_string(
    settings.APPLICATIONINSIGHTS_CONNECTION_STRING
)

_meter_provider = MeterProvider(
    metric_readers=[
        PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
    ]
)


# log
log_exporter = AzureMonitorLogExporter.from_connection_string(
    settings.APPLICATIONINSIGHTS_CONNECTION_STRING
)

_log_emitter_provider = LoggerProvider()
_log_emitter_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

azure_monitor_handler = LoggingHandler(
    logger_provider=_log_emitter_provider,
)


def init_azure_monitor():
    trace.set_tracer_provider(_trace_provider)
    metrics.set_meter_provider(_meter_provider)
    set_logger_provider(_log_emitter_provider)
