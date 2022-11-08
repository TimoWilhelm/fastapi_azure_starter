FROM python:3.11-bullseye as requirements

ENV POETRY_VERSION=1.2.2

WORKDIR /tmp

RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN pip install --no-cache-dir --upgrade -r requirements.txt


FROM python:3.11-slim-bullseye

ENV LANG C.UTF-8 \
    LC_ALL C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random

COPY --from=requirements /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /run

COPY gunicorn.conf.py .
COPY alembic.ini .
COPY ./alembic ./alembic
COPY ./app ./app

# Creates a non-root user with an explicit UID and adds permission to access the /run folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /run
USER appuser

EXPOSE 8080

CMD ["gunicorn", "app.main:app", "--config=./gunicorn.conf.py", "--bind=0.0.0.0:8080"]
