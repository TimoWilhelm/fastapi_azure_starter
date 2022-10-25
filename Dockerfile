FROM python:3.11-bullseye as requirements

ENV POETRY_VERSION=1.2.2

WORKDIR /tmp

RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ./
RUN poetry export --format requirements.txt --output requirements.txt --without-hashes

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install --no-cache-dir --upgrade "uvicorn[standard]"


FROM python:3.11-slim-bullseye

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

COPY --from=requirements /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./app /app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host=0.0.0.0", "--port=8080"]
