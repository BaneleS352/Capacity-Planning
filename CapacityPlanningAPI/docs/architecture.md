# Backend Architecture

## Shape

The backend is a FastAPI modular monolith with explicit domain, application, and
infrastructure boundaries. HTTP handlers validate and authorize, application services
coordinate use cases, pure domain services implement calculations, and repositories own
database access. Celery workers call the same application services as HTTP-triggered jobs.

```text
Client -> FastAPI -> application services -> repositories -> PostgreSQL
                  -> domain engines
Webhook -> durable event -> Celery worker -> normalization/recalculation
Read API -> precomputed summaries/cache -> client
```

## Modules

- `app/api`: versioned routers, dependencies, pagination, and error contracts.
- `app/core`: settings, OIDC/JWT security, RBAC, logging, telemetry, and exceptions.
- `app/domain`: framework-independent value objects, capacity engine, and risk engine.
- `app/application`: dashboard, planning, integration, and administration use cases.
- `app/infrastructure`: SQLAlchemy persistence, external clients, caching, and workers.
- `app/models`: persisted operational, integration, planning, analytics, and audit models.
- `app/schemas`: public request/response contracts.

## CQRS and consistency

Transactional normalized tables form the write model. Capacity summaries, risk summaries,
and dashboard records form query-oriented read models. A transactional outbox records
domain events in the same transaction as source changes; workers claim and process events
idempotently. Dashboard reads may be eventually consistent and always return source and
calculation timestamps.

## Runtime topology

- API container: FastAPI/Uvicorn behind an API gateway or load balancer.
- Worker container: Celery consumers for sync, webhook processing, snapshots, and metrics.
- Scheduler: Celery Beat or a cloud scheduler for incremental and reconciliation jobs.
- PostgreSQL: durable operational and analytics store.
- Redis/RabbitMQ: broker; Redis may additionally cache read models and rate limits.
- Object storage: encrypted raw integration payload archives with retention policies.
- Entra ID/other OIDC provider: authentication and MFA.

## API conventions

- Prefix all business endpoints with `/api/v1`.
- Return resource schemas directly for success and RFC 7807-compatible problem details
  for failures.
- Use UUID identifiers, UTC timestamps, optimistic update timestamps, bounded pagination,
  allowlisted sort fields, and explicit filters.
- `POST` creates or triggers, `PUT` replaces, `PATCH` partially updates, and `DELETE`
  retires/deletes where policy allows.
- Webhook responses acknowledge only after signature/idempotency validation and durable
  event persistence; processing is asynchronous.

## Deployment safeguards

Production startup rejects disabled authentication, placeholder webhook secrets, and
SQLite database URLs. Readiness checks verify the database. Schema changes run as a
separate Alembic deployment step, never implicitly from application startup.

