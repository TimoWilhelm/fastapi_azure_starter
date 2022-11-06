import logging

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

span_processor = BatchSpanProcessor(trace_exporter)
provider = TracerProvider(sampler=TraceIdRatioBased(settings.TRACING_SAMPLER_RATE))
provider.add_span_processor(span_processor)
trace.set_tracer_provider(provider)


# metric
metric_exporter = AzureMonitorMetricExporter.from_connection_string(
    settings.APPLICATIONINSIGHTS_CONNECTION_STRING
)

reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))


# log
log_exporter = AzureMonitorLogExporter.from_connection_string(
    settings.APPLICATIONINSIGHTS_CONNECTION_STRING
)

log_emitter_provider = LoggerProvider()
log_processor = BatchLogRecordProcessor(log_exporter)
log_emitter_provider.add_log_record_processor(log_processor)
set_logger_provider(log_emitter_provider)

azure_monitor_handler = LoggingHandler(
    level=logging._nameToLevel[settings.LOG_LEVEL],
    logger_provider=log_emitter_provider,
)
