# FastAPI Starter

This repository is a batteries included starter project template for the FastAPI framework with the following features:

- Multi-worker hosting with [Gunicorn](https://docs.gunicorn.org)
- [Azure AD OpenID Connect](https://learn.microsoft.com/azure/active-directory/fundamentals/auth-oidc) user authentication and role-based authorization
- [OpenTelemetry](https://opentelemetry.io/) monitoring with Azure Application Insights integration
- Rate limiting with [SlowApi](https://slowapi.readthedocs.io/en/latest/)
- SQL Database integration with [SQLAlchemy 2.0](https://www.sqlalchemy.org/) and [asyncpg](https://github.com/MagicStack/asyncpg)
- Docker container packaging

# Requirements:

- [Python 3.11](https://www.python.org/) (can be installed from the [Windows Store](https://apps.microsoft.com/store/detail/python-311/9NRWMJP3717K))
- [Python Poetry](https://python-poetry.org/docs/) package manager.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [PowerShell](https://github.com/PowerShell/PowerShell/)

If you are using [Visual Studio Code](https://code.visualstudio.com/), install the [recommended extensions](./.vscode/extensions.json).

# Setup

Run the [Setup Script](./scripts/Setup-Dependencies.ps1) to install the project dependencies.
This will also create a Python virtual environment you can activate using the `activate` scripts in the [venv scripts](./.venv/scripts/) folder.

> Make sure to update your editor settings to use the virtual environment to enable linting and autoformatting!

# Debugging

Update or create an [./.env](.env) file containing your local environment settings.

The following settings are required to start the application.

```env
TENANT_ID= # Your Azure AD Tenant ID
API_CLIENT_ID= # The Azure AD Application ID used by your API
OPENAPI_CLIENT_ID= # The Azure AD Application ID used by the OpenAPI frontend
```

You can find additional configuration options in the [config.py](./app/config.py) file.

Run the following docker command or use the [tasks](./.vscode/tasks.json) to setup your local docker environment.

```bash
docker compose -f docker-compose.debug.yml up -d
```

After the containers are running you will be able to attach the debugger to the API and set breakpoints using the [Python: Remote Attach](./.vscode/launch.json) launch configuration. The Python debugger will be listening on port `5678`.

You can open your browser at [localhost:5050](http://localhost:5050) to connect to your local database using [pgAdmin](https://www.pgadmin.org/) with the following credentials.

```
Username: admin@pgadmin.org
Password: admin
```

The default database is `main`. To connect to the pre-configured postgres server use the following credentials.

```
Username: postgres
Password: postgres
```

# Migrations

Create [automatic revisions](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) from your [SQLAlchemy ORM models](https://docs.sqlalchemy.org/en/20/orm/quickstart.html#declare-models).

```bash
alembic revision --autogenerate -m "Descriptive Message"
```

Migrations will automatically be applied on the next application start or can be manually applied using the following command.

```bash
alembic upgrade head
```
