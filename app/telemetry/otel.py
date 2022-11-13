from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor


def patch_otel(enable_system_metrics=False):
    LoggingInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()

    if enable_system_metrics:  # pragma: NO COVER
        SystemMetricsInstrumentor().instrument()
