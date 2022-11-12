from uvicorn.workers import UvicornWorker


class HeadlessUvicornWorker(UvicornWorker):
    # https://www.uvicorn.org/settings/
    CONFIG_KWARGS = {
        "server_header": False,
    }
