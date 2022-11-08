# import settings first so it can be used by other modules
from .settings import settings  # noqa isort:skip

from .azure_scheme import azure_scheme
from .database import get_db
from .limiter import limiter

__all__ = ["settings", "get_db", "azure_scheme", "limiter"]


# Side effects

from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor

from .util.logging import init_logging
from .util.otel import init_azure_monitor

init_logging()
init_azure_monitor()

LoggingInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()
RedisInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument()

if settings.SYSTEM_METRICS_ENABLED:
    SystemMetricsInstrumentor().instrument()
