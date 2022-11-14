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


class AzureMonitor:
    _log_emitter_provider = LoggerProvider()

    azure_monitor_log_handler = LoggingHandler(
        logger_provider=_log_emitter_provider,
    )

    @classmethod
    def init(cls, connection_string: str, tracing_sampler_rate=1.0):
        # trace
        trace_exporter = AzureMonitorTraceExporter.from_connection_string(
            connection_string
        )

        trace_provider = TracerProvider(sampler=TraceIdRatioBased(tracing_sampler_rate))
        trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

        trace.set_tracer_provider(trace_provider)

        # metric
        metric_exporter = AzureMonitorMetricExporter.from_connection_string(
            connection_string
        )

        meter_provider = MeterProvider(
            metric_readers=[
                PeriodicExportingMetricReader(
                    metric_exporter, export_interval_millis=5000
                )
            ]
        )

        metrics.set_meter_provider(meter_provider)

        # log
        log_exporter = AzureMonitorLogExporter.from_connection_string(connection_string)

        cls._log_emitter_provider.add_log_record_processor(
            BatchLogRecordProcessor(log_exporter)
        )

        set_logger_provider(cls._log_emitter_provider)
