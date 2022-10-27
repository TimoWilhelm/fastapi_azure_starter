# import settings first so it can be used by other modules
from .settings import settings  # noqa isort:skip

from .azure_scheme import azure_scheme
from .limiter import limiter

__all__ = ["settings", "azure_scheme", "limiter"]

from .util.logging import init_logging

init_logging()
