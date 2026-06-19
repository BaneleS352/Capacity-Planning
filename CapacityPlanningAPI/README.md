# Capacity Planning API

Production-oriented FastAPI backend for engineering capacity planning. It combines Jira
delivery work, PaySpace employee/leave data, sprint snapshots, configurable capacity
rules, team velocity, and persistent delivery-risk signals.

## Architecture

- Python 3.12+, FastAPI, Pydantic, async SQLAlchemy, PostgreSQL, and Alembic.
- Clean modular monolith with pure capacity/risk domain engines.
- Celery workers, Redis broker/cache, and a transactional outbox.
- OIDC JWT validation with role and team-level authorization.
- Signed, replay-protected Jira and PaySpace webhook endpoints.
- RFC 7807 problem responses, correlation IDs, JSON logs, audit records, and freshness
  indicators.

The extracted product requirements and explicit assumptions are in
[`docs/requirements.md`](docs/requirements.md). Architectural decisions are in
[`docs/architecture.md`](docs/architecture.md).

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
python -m app.cli seed-demo
uvicorn app.main:app --reload
```

Open `http://localhost:8000/api/v1/docs`. No `.env` file or bearer token is required in
local development: unauthenticated requests use the first active organization as a local
system administrator. The seed command still prints an optional development token for
testing authenticated clients. Local authentication is rejected by staging and production
configuration validation.

### Demo data

Populate a realistic, idempotent demo workspace:

```powershell
python -m app.cli seed-demo
```

This creates three engineering teams, fourteen employees, effective-dated memberships, leave,
a public holiday, fifteen historical sprints, three active sprints, Jira issues, identity and
field mappings, integration freshness records, historical velocity/capacity, and current
risk signals. It runs the production capacity and risk engines after insertion and prints
a fresh local system-admin token. Re-running the command recalculates the active sprints
without duplicating demo records.

## Containers

```powershell
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.cli seed --slug demo --name "Demo Organization"
```

Services:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Verification

```powershell
ruff check .
mypy app
pytest --cov=app --cov-report=term-missing
alembic check
```

## Important endpoints

- `GET /api/v1/teams/{team_id}/dashboard?sprint_id=...`
- `GET /api/v1/teams/{team_id}/capacity?sprint_id=...`
- `GET /api/v1/employees/{employee_id}/profile`
- `GET /api/v1/sprints/{sprint_id}/timeline`
- `GET /api/v1/reports/planned-vs-actual?team_id=...`
- `POST /api/v1/integrations/jira/webhook`
- `POST /api/v1/integrations/payspace/webhook`
- `POST /api/v1/admin/recalculate-capacity`

Jira and PaySpace are external systems of record. Do not place credentials in integration
configuration JSON; store only a secrets-manager reference in `secret_reference`.

## Webhook signing

Webhook callers send `X-Organization-ID`, `X-Webhook-ID`, `X-Webhook-Event`,
`X-Webhook-Timestamp`, and `X-Webhook-Signature`. The signature is the lowercase hex
HMAC-SHA256 of `<unix_timestamp>.<raw_body>` using the configured source secret. The API
rejects stale timestamps and duplicate event IDs are acknowledged idempotently.

## Database lifecycle

Application startup never creates or changes tables. Run Alembic as a deployment step.
The default SQLite URL is for local development and tests only; staging/production settings
reject it and require OIDC authentication plus strong webhook secrets.

### SQL Server LocalDB

The API accepts an ADO.NET connection string from the deployment process and converts it to
the async SQLAlchemy ODBC URL used by both the application and Alembic. For a PowerShell
session using the local `betteams` database, set:

```powershell
$env:DATABASE_CONNECTION_STRING = 'Server=(localdb)\MSSQLLocalDB;Database=betteams;Trusted_Connection=True;MultipleActiveResultSets=true'
$env:DATABASE_ODBC_DRIVER = 'ODBC Driver 18 for SQL Server'
```

Then run `alembic upgrade head`. Jira issues, PaySpace employees and leave, signed webhook
payloads, integration runs, capacity calculations, and risk signals are persisted through
the existing transactional SQLAlchemy services.
