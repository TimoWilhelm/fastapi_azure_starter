FROM python:3.11-bullseye as requirements

ENV POETRY_VERSION=1.2.2

WORKDIR /tmp

RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade -r requirements.txt


FROM python:3.11-slim-bullseye

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

COPY --from=requirements /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY gunicorn.conf.py /
COPY ./app /app

EXPOSE 8080

# TODO: ENV OTEL_EXPORTER_OTLP_ENDPOINT=""

ENV OTEL_PYTHON_EXCLUDED_URLS="health,oauth2-redirect"
ENV OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST="Accept-Encoding,User-Agent,Referer"
ENV OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE="Last-Modified,Content-Type"

CMD [ \
    # TODO: "opentelemetry-instrument", "--traces_exporter=otlp", "--metrics_exporter=otlp", "--logs_exporter=otlp", \
    "opentelemetry-instrument", "--traces_exporter=none", "--metrics_exporter=none", "--logs_exporter=console", \
    "gunicorn", "app.main:app", "--config=./gunicorn.conf.py", "--worker-class=app.worker.HeadlessUvicornWorker", "--bind=0.0.0.0:8080" \
    ]
