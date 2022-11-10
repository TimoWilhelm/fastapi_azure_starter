# import settings first so it can be used by other modules
from .settings import settings  # isort:skip


# patch telemetry before importing other modules
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor

LoggingInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()
RedisInstrumentor().instrument()
AsyncPGInstrumentor().instrument()

if settings.SYSTEM_METRICS_ENABLED:
    SystemMetricsInstrumentor().instrument()


# setup logging
from .util.logging import init_logging  # noqa: E402
from .util.otel import init_azure_monitor  # noqa: E402

init_logging()
init_azure_monitor()

# global modules
from .azure_scheme import azure_scheme  # noqa: E402
from .limiter import limiter  # noqa: E402

__all__ = ["settings", "azure_scheme", "limiter"]
