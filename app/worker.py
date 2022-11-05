from uvicorn.workers import UvicornWorker

from app import settings


class HeadlessUvicornWorker(UvicornWorker):
    # https://www.uvicorn.org/settings/
    CONFIG_KWARGS = {"log_level": settings.LOG_LEVEL.lower(), "server_header": False}
