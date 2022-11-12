from app.config import get_settings

# https://docs.gunicorn.org/en/stable/settings.html

loglevel = get_settings().GUNICORN_LOG_LEVEL.lower()
errorlog = "-"  # stderr
accesslog = "-"  # stdout

workers = get_settings().WORKER_COUNT
worker_class = "app.gunicorn_worker.HeadlessUvicornWorker"
preload_app = True

timeout = 30
keepalive = 24 * 60 * 60  # 1 day because the app is deployed behind a load balancer
