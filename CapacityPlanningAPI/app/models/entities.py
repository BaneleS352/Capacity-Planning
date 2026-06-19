from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SprintState(StrEnum):
    FUTURE = "future"
    ACTIVE = "active"
    CLOSED = "closed"


class IntegrationSource(StrEnum):
    JIRA = "jira"
    PAYSPACE = "payspace"


class IntegrationRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class RiskSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SnapshotType(StrEnum):
    START = "start"
    DAILY = "daily"
    COMPLETE = "complete"
    MANUAL = "manual"
    SCOPE_CHANGED = "scope_changed"
    LEAVE_CHANGED = "leave_changed"


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    external_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "external_subject",
            name="uq_users_organization_id_external_subject",
        ),
        UniqueConstraint("organization_id", "email", name="uq_users_organization_id_email"),
    )


class Team(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(String(200), index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    location_code: Mapped[str | None] = mapped_column(String(32), index=True)
    velocity_lookback: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    working_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("8.00"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (UniqueConstraint("organization_id", "slug"),)


class TeamAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    access_type: Mapped[str] = mapped_column(String(50), default="assigned", nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "team_id"),)


class Employee(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    payspace_employee_number: Mapped[str | None] = mapped_column(String(100), index=True)
    jira_account_id: Mapped[str | None] = mapped_column(String(255), index=True)
    corporate_email: Mapped[str] = mapped_column(String(320), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    role_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    department: Mapped[str | None] = mapped_column(String(200), index=True)
    manager_employee_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), index=True
    )
    employment_type: Mapped[str] = mapped_column(String(50), default="employee", nullable=False)
    location_code: Mapped[str | None] = mapped_column(String(32), index=True)
    contract_hours_per_day: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("8.00"), nullable=False
    )
    fte_factor: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), default=Decimal("1.000"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("organization_id", "corporate_email"),)


class TeamMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    allocation_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100.00"), nullable=False
    )
    delivery_role: Mapped[str | None] = mapped_column(String(120), index=True)
    critical_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)

    __table_args__ = (Index("ix_team_membership_effective", "team_id", "start_date", "end_date"),)


class LeaveRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    leave_type: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    partial_day_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String(30), default="approved", nullable=False, index=True)
    source_reference_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("employee_id", "source_reference_id"),
        Index("ix_leave_employee_dates", "employee_id", "start_date", "end_date"),
    )


class PublicHoliday(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    location_code: Mapped[str] = mapped_column(String(32), nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    __table_args__ = (UniqueConstraint("organization_id", "location_code", "holiday_date"),)


class CapacityProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role_name: Mapped[str] = mapped_column(String(120), nullable=False)
    daily_focus_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    ceremony_hours_per_sprint: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    meeting_buffer_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("10"), nullable=False
    )
    support_buffer_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("5"), nullable=False
    )
    review_buffer_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("5"), nullable=False
    )
    unplanned_buffer_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("10"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("organization_id", "role_name"),)


class Sprint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    jira_sprint_id: Mapped[str | None] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[SprintState] = mapped_column(
        Enum(SprintState, native_enum=False, length=20), index=True, nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    goal: Mapped[str | None] = mapped_column(Text)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("team_id", "jira_sprint_id"),)


class JiraIssue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sprint_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sprints.id", ondelete="SET NULL"), index=True
    )
    jira_site_id: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    assignee_employee_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status_category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    priority: Mapped[str | None] = mapped_column(String(50), index=True)
    issue_type: Mapped[str | None] = mapped_column(String(80), index=True)
    epic_key: Mapped[str | None] = mapped_column(String(50), index=True)
    story_points: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0"), nullable=False
    )
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    blocked_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    added_to_sprint_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_from_sprint_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    normalized_fields: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (UniqueConstraint("organization_id", "jira_site_id", "external_id"),)


class JiraFieldMapping(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    jira_site_id: Mapped[str] = mapped_column(String(100), nullable=False)
    logical_field: Mapped[str] = mapped_column(String(100), nullable=False)
    jira_field_id: Mapped[str] = mapped_column(String(100), nullable=False)
    transformation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (UniqueConstraint("organization_id", "jira_site_id", "logical_field"),)


class IdentityMapping(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    jira_account_id: Mapped[str | None] = mapped_column(String(255), index=True)
    payspace_employee_number: Mapped[str | None] = mapped_column(String(100), index=True)
    corporate_email: Mapped[str | None] = mapped_column(String(320), index=True)
    status: Mapped[str] = mapped_column(
        String(30), default="unresolved", nullable=False, index=True
    )
    match_method: Mapped[str | None] = mapped_column(String(50))
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class SprintCommitmentSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    sprint_id: Mapped[UUID] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), index=True, nullable=False
    )
    snapshot_type: Mapped[SnapshotType] = mapped_column(
        Enum(SnapshotType, native_enum=False, length=30), nullable=False
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    issue_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    committed_story_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    added_story_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    removed_story_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    completed_story_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class EmployeeCapacitySnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    sprint_id: Mapped[UUID] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    working_days: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    gross_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    leave_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    holiday_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ceremony_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    buffer_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    net_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    effective_person_days: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    assigned_story_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (UniqueConstraint("sprint_id", "employee_id"),)


class TeamCapacitySummary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "team_capacity_summaries"

    sprint_id: Mapped[UUID] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available_hours: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    effective_person_days: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    leave_impact_hours: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    story_points_per_effective_day: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    story_point_capacity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    committed_story_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    added_story_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    removed_story_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    completed_story_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    in_progress_story_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    remaining_story_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    utilization_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    risk_level: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    inputs_fresh_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TeamVelocityMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sprint_id: Mapped[UUID] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    completed_story_points: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    effective_person_days: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    story_points_per_effective_day: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))


class RiskThreshold(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    team_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True
    )
    risk_type: Mapped[str] = mapped_column(String(80), nullable=False)
    warning_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    critical_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RiskSignal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sprint_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"), index=True
    )
    risk_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    severity: Mapped[RiskSeverity] = mapped_column(
        Enum(RiskSeverity, native_enum=False, length=20), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class IntegrationConfiguration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source: Mapped[IntegrationSource] = mapped_column(
        Enum(IntegrationSource, native_enum=False, length=20), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    secret_reference: Mapped[str | None] = mapped_column(String(500))

    __table_args__ = (UniqueConstraint("organization_id", "source", "name"),)


class IntegrationRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source: Mapped[IntegrationSource] = mapped_column(
        Enum(IntegrationSource, native_enum=False, length=20), index=True, nullable=False
    )
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[IntegrationRunStatus] = mapped_column(
        Enum(IntegrationRunStatus, native_enum=False, length=20), index=True, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_read: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_written: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text)
    cursor: Mapped[str | None] = mapped_column(String(500))


class WebhookEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source: Mapped[IntegrationSource] = mapped_column(
        Enum(IntegrationSource, native_enum=False, length=20), index=True, nullable=False
    )
    external_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    processing_error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("organization_id", "source", "external_event_id"),)


class DashboardReadModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    sprint_id: Mapped[UUID | None] = mapped_column(index=True)
    model_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "resource_type", "resource_id", "sprint_id"),
    )


class OutboxEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[UUID | None] = mapped_column(index=True)
    event_type: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)


class AuditLog(UUIDPrimaryKeyMixin, Base):
    organization_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    actor_subject: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100))
    team_id: Mapped[UUID | None] = mapped_column(index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    correlation_id: Mapped[str | None] = mapped_column(String(128))
    ip_address_hash: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
