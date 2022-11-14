from app.config import get_settings
from app.telemetry.azure_monitor import AzureMonitor
from app.telemetry.otel import patch_otel

settings = get_settings()

# https://docs.gunicorn.org/en/stable/settings.html

loglevel = settings.GUNICORN_LOG_LEVEL.lower()
errorlog = "-"  # stderr
accesslog = "-"  # stdout

workers = settings.WORKER_COUNT
worker_class = "app.gunicorn_worker.HeadlessUvicornWorker"
preload_app = True

timeout = 30
keepalive = 24 * 60 * 60  # 1 day because the app is deployed behind a load balancer


def post_fork(server, worker):
    server.log.info("Worker spawned with PID: %s", worker.pid)

    patch_otel(enable_system_metrics=settings.SYSTEM_METRICS_ENABLED)
    server.log.info("Applied OpenTelemetry Instrumentation")

    if settings.APPLICATIONINSIGHTS_CONNECTION_STRING is not None:
        AzureMonitor.init(
            settings.APPLICATIONINSIGHTS_CONNECTION_STRING,
            tracing_sampler_rate=settings.TRACING_SAMPLER_RATE,
        )
        server.log.info("Initialized Azure Monitor Exporter")
