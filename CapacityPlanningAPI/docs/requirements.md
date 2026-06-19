# Capacity Planning Backend Requirements

## Product goal

Provide an enterprise capacity and delivery-risk API that combines Jira delivery data,
PaySpace workforce/leave data, and locally governed planning rules. Jira remains the
source of truth for delivery work and PaySpace remains the source of truth for employee
and leave data. This service is the source of truth for mappings, planning assumptions,
capacity results, sprint snapshots, risks, and historical analytics.

## Actors and authorization

| Role | Scope |
| --- | --- |
| Software Development Manager | Employee and delivery detail for managed teams |
| Senior Manager / Head of Engineering | Multiple teams or a department |
| Scrum Master / Delivery Lead | Assigned teams and sprint planning data |
| Product Owner | Delivery visibility with restricted HR detail |
| HR Admin | Employee and permitted leave detail |
| System Admin | Global configuration, integrations, mappings, and access |
| Executive | Aggregated reports; no sensitive employee detail by default |

Authorization combines RBAC with explicit team access. Leave availability and leave
reason access are separate permissions. Employee profile reads and administrative
changes are audited.

## Functional requirements

- Manage organizations, teams, team memberships, access grants, employees, roles,
  reporting lines, capacity profiles, public holidays, and sprint configuration.
- Map Jira account IDs, corporate email addresses, and PaySpace employee numbers;
  expose unresolved and conflicting mappings for administration.
- Ingest Jira boards, projects, sprints, issues, changes, and webhooks. Story-point,
  blocked, and status fields must be tenant-configurable.
- Ingest PaySpace employees and leave through API/webhook adapters, with CSV/SFTP as
  a later adapter using the same normalized contracts.
- Snapshot sprint commitments at start and track work added, removed, completed, and
  carried over. Preserve daily and completion snapshots for historical reporting.
- Calculate gross and effective employee/team capacity, leave and holiday impact,
  utilization, and team-specific story-point capacity based on historical velocity.
- Emit structured, persistent risk signals for over/under-capacity, leave impact,
  critical-role absence, blocked work, scope creep, unassigned priority work, stale
  data, recurring carry-over, and mapping errors.
- Return dashboard-optimized team, employee, sprint, risk, and reporting read models.
- Track integration runs, source freshness, failures, webhook idempotency, and audit
  events. Continue serving last-known data with explicit stale indicators.
- Support pagination, filtering, sorting, search, stable error contracts, API versioning,
  OpenAPI documentation, health/readiness endpoints, and correlation IDs.

## Capacity rules

1. Working days are weekdays inside the inclusive sprint interval, excluding configured
   public holidays for the employee's location.
2. Gross hours are working days multiplied by contract hours and FTE factor.
3. Approved leave removes overlapping working-day hours. Holidays are not deducted a
   second time.
4. Fixed ceremony hours and configurable meeting, admin, support, review, and unplanned
   work percentages are deducted from available hours. Net capacity is never negative.
5. Team capacity is the sum of member capacity during effective-dated memberships.
6. Story-point capacity uses completed story points divided by effective person-days
   across a configurable lookback, defaulting to five completed sprints. It is a team
   planning measure, never an individual performance ranking.
7. Utilization is planned story-point load divided by story-point capacity. When no
   reliable velocity exists, hour capacity is still returned and utilization is unknown.

## Default risk thresholds

- Utilization below 70 percent: under-capacity / possible under-planning.
- 70 through 95 percent: healthy.
- Above 95 through 110 percent: watch.
- Above 110 percent: over-capacity.
- Critical-role absence over 25 percent of sprint: delivery risk.
- Work added after sprint start over 20 percent: scope-change risk.
- Not-started story points over 30 percent after sprint midpoint: delivery risk.
- Blocked for more than two working days: dependency risk.
- High-priority work without an assignee: planning risk.

All thresholds are organization/team configurable; defaults are seeded, not hardcoded
into API handlers.

## Security and resilience

- Validate short-lived OIDC JWTs against configured issuer, audience, and JWKS.
- Require TLS at the edge, least-privilege integration credentials, secrets-manager
  injection, webhook signatures, replay protection, and optional IP allowlisting.
- Encrypt infrastructure at rest; never store salary, medical notes, documents,
  disciplinary records, or personal identity documents.
- Mask leave reasons by default and log metadata rather than source payloads.
- Use idempotent jobs/webhooks, exponential retry, partial-sync recovery, dead-letter
  handling, pagination-aware incremental sync, nightly reconciliation, and source
  freshness warnings.
- Partition/archive high-volume history and raw payloads in production; keep normalized
  operational data in PostgreSQL and raw archives in object storage.

## Assumptions and ambiguities

- The PDF is a product/architecture specification, not an exact external API contract.
  Jira and PaySpace tenant URLs, credentials, field IDs, webhook formats, and PaySpace
  signing rules are supplied through configuration and field mappings.
- Public holiday calendars are maintained locally unless a tenant adapter supplies them.
- A leave period is date-based and consumes the employee's normal daily contract hours;
  optional partial-day hours override the full-day value.
- Percentage buffers apply after holidays and leave, while fixed ceremony hours are
  deducted before percentage buffers. This prevents holiday and leave double counting.
- Sprint start snapshots are authoritative for committed scope. An issue's first-seen
  timestamp after sprint start marks added scope; removal is recorded as an event rather
  than inferred only from current Jira state.
- The service is multi-organization at the data-model and authorization layers. Each
  authenticated user operates in one organization per request.
- Exact labor-law and privacy policy varies by jurisdiction. The API stores only the
  minimum leave fields and exposes detailed reasons solely with `leave:reason:read`.
- Phase 4 predictive/AI features and vendor-specific SFTP/data-warehouse adapters are
  extension points, not part of the first operational release. Core MVP through Phase 3
  data contracts, calculations, reports, and governance are implemented here.

