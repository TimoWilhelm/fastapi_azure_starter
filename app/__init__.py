from .azure_scheme import azure_scheme
from .limiter import limiter
from .settings import settings

__all__ = ["settings", "azure_scheme", "limiter"]

from .util.logging import init_logging

init_logging()
