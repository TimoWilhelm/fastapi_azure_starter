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

from app.config import get_settings

azure_monitor_handler: logging.Handler | None = None


def init_azure_monitor():  # pragma: NO COVER
    global azure_monitor_handler

    ai_connection_string = get_settings().APPLICATIONINSIGHTS_CONNECTION_STRING

    # trace
    trace_exporter = AzureMonitorTraceExporter.from_connection_string(
        ai_connection_string
    )

    trace_provider = TracerProvider(
        sampler=TraceIdRatioBased(get_settings().TRACING_SAMPLER_RATE)
    )
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

    # metric
    metric_exporter = AzureMonitorMetricExporter.from_connection_string(
        ai_connection_string
    )

    meter_provider = MeterProvider(
        metric_readers=[
            PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
        ]
    )

    # log
    log_exporter = AzureMonitorLogExporter.from_connection_string(ai_connection_string)

    log_emitter_provider = LoggerProvider()
    log_emitter_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

    azure_monitor_handler = LoggingHandler(
        logger_provider=log_emitter_provider,
    )

    trace.set_tracer_provider(trace_provider)
    metrics.set_meter_provider(meter_provider)
    set_logger_provider(log_emitter_provider)
