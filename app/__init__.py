# import settings first so it can be used by other modules
from .settings import settings  # noqa isort:skip

from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor

from .azure_scheme import azure_scheme
from .limiter import limiter

__all__ = ["settings", "azure_scheme", "limiter"]

from .util.logging import init_logging

init_logging()

LoggingInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()
RedisInstrumentor().instrument()

if settings.SYSTEM_METRICS_ENABLED:
    SystemMetricsInstrumentor().instrument()
