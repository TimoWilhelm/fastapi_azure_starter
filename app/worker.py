from uvicorn.workers import UvicornWorker


class HeadlessUvicornWorker(UvicornWorker):
    # for more settings, see: https://www.uvicorn.org/settings/
    CONFIG_KWARGS = {"server_header": False}
