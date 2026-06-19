from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.security import Role
from app.models.entities import IntegrationRunStatus, IntegrationSource, RiskSeverity, SprintState


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    timezone: str = Field(default="UTC", max_length=64)


class OrganizationRead(ORMModel):
    id: UUID
    name: str
    slug: str
    timezone: str
    active: bool
    created_at: datetime
    updated_at: datetime


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    department: str | None = Field(default=None, max_length=200)
    timezone: str = Field(default="UTC", max_length=64)
    location_code: str | None = Field(default=None, max_length=32)
    velocity_lookback: int = Field(default=5, ge=1, le=20)
    working_hours_per_day: Decimal = Field(default=Decimal("8"), gt=0, le=24)
    settings: dict[str, Any] = Field(default_factory=dict)


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    department: str | None = Field(default=None, max_length=200)
    timezone: str | None = Field(default=None, max_length=64)
    location_code: str | None = Field(default=None, max_length=32)
    velocity_lookback: int | None = Field(default=None, ge=1, le=20)
    working_hours_per_day: Decimal | None = Field(default=None, gt=0, le=24)
    active: bool | None = None
    settings: dict[str, Any] | None = None


class TeamRead(ORMModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    department: str | None
    timezone: str
    location_code: str | None
    velocity_lookback: int
    working_hours_per_day: Decimal
    active: bool
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class EmployeeCreate(BaseModel):
    payspace_employee_number: str | None = Field(default=None, max_length=100)
    jira_account_id: str | None = Field(default=None, max_length=255)
    corporate_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    full_name: str = Field(min_length=1, max_length=200)
    role_name: str = Field(min_length=1, max_length=120)
    department: str | None = Field(default=None, max_length=200)
    manager_employee_id: UUID | None = None
    employment_type: str = Field(default="employee", max_length=50)
    location_code: str | None = Field(default=None, max_length=32)
    contract_hours_per_day: Decimal = Field(default=Decimal("8"), gt=0, le=24)
    fte_factor: Decimal = Field(default=Decimal("1"), gt=0, le=1)


class EmployeeUpdate(BaseModel):
    payspace_employee_number: str | None = Field(default=None, max_length=100)
    jira_account_id: str | None = Field(default=None, max_length=255)
    corporate_email: str | None = Field(
        default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320
    )
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    role_name: str | None = Field(default=None, min_length=1, max_length=120)
    department: str | None = Field(default=None, max_length=200)
    manager_employee_id: UUID | None = None
    employment_type: str | None = Field(default=None, max_length=50)
    location_code: str | None = Field(default=None, max_length=32)
    contract_hours_per_day: Decimal | None = Field(default=None, gt=0, le=24)
    fte_factor: Decimal | None = Field(default=None, gt=0, le=1)
    active: bool | None = None


class EmployeeRead(ORMModel):
    id: UUID
    organization_id: UUID
    payspace_employee_number: str | None
    jira_account_id: str | None
    corporate_email: str
    full_name: str
    role_name: str
    department: str | None
    manager_employee_id: UUID | None
    employment_type: str
    location_code: str | None
    contract_hours_per_day: Decimal
    fte_factor: Decimal
    active: bool
    source_updated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MembershipCreate(BaseModel):
    employee_id: UUID
    allocation_percent: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    delivery_role: str | None = Field(default=None, max_length=120)
    critical_role: bool = False
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def dates_are_ordered(self):  # type: ignore[no-untyped-def]
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class MembershipRead(ORMModel):
    id: UUID
    team_id: UUID
    employee_id: UUID
    allocation_percent: Decimal
    delivery_role: str | None
    critical_role: bool
    start_date: date
    end_date: date | None


class LeaveCreate(BaseModel):
    employee_id: UUID
    start_date: date
    end_date: date
    leave_type: str = Field(min_length=1, max_length=100)
    reason: str | None = Field(default=None, max_length=2000)
    partial_day_hours: Decimal | None = Field(default=None, gt=0, le=24)
    status: str = Field(default="approved", max_length=30)
    source_reference_id: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def dates_are_ordered(self):  # type: ignore[no-untyped-def]
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class LeaveRead(ORMModel):
    id: UUID
    employee_id: UUID
    start_date: date
    end_date: date
    leave_type: str
    reason: str | None
    partial_day_hours: Decimal | None
    status: str
    source_reference_id: str
    source_updated_at: datetime | None


class PublicHolidayCreate(BaseModel):
    location_code: str = Field(min_length=1, max_length=32)
    holiday_date: date
    name: str = Field(min_length=1, max_length=200)


class PublicHolidayRead(ORMModel):
    id: UUID
    organization_id: UUID
    location_code: str
    holiday_date: date
    name: str


class CapacityProfileUpsert(BaseModel):
    role_name: str = Field(min_length=1, max_length=120)
    daily_focus_hours: Decimal | None = Field(default=None, gt=0, le=24)
    ceremony_hours_per_sprint: Decimal = Field(default=Decimal("0"), ge=0, le=200)
    meeting_buffer_percent: Decimal = Field(default=Decimal("10"), ge=0, le=100)
    support_buffer_percent: Decimal = Field(default=Decimal("5"), ge=0, le=100)
    review_buffer_percent: Decimal = Field(default=Decimal("5"), ge=0, le=100)
    unplanned_buffer_percent: Decimal = Field(default=Decimal("10"), ge=0, le=100)

    @model_validator(mode="after")
    def total_buffer_is_valid(self):  # type: ignore[no-untyped-def]
        total = (
            self.meeting_buffer_percent
            + self.support_buffer_percent
            + self.review_buffer_percent
            + self.unplanned_buffer_percent
        )
        if total > 100:
            raise ValueError("Combined buffers cannot exceed 100 percent")
        return self


class CapacityProfileRead(CapacityProfileUpsert, ORMModel):
    id: UUID
    organization_id: UUID
    active: bool


class SprintCreate(BaseModel):
    team_id: UUID
    jira_sprint_id: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    state: SprintState
    start_at: datetime
    end_at: datetime
    goal: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def dates_are_ordered(self):  # type: ignore[no-untyped-def]
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class SprintUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    state: SprintState | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    completed_at: datetime | None = None
    goal: str | None = Field(default=None, max_length=4000)


class SprintRead(ORMModel):
    id: UUID
    team_id: UUID
    jira_sprint_id: str | None
    name: str
    state: SprintState
    start_at: datetime
    end_at: datetime
    completed_at: datetime | None
    goal: str | None
    source_updated_at: datetime | None


class JiraIssueUpsert(BaseModel):
    sprint_id: UUID | None = None
    jira_site_id: str = Field(min_length=1, max_length=100)
    external_id: str = Field(min_length=1, max_length=100)
    issue_key: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=1, max_length=4000)
    assignee_employee_id: UUID | None = None
    status: str = Field(min_length=1, max_length=100)
    status_category: str = Field(min_length=1, max_length=30)
    priority: str | None = Field(default=None, max_length=50)
    issue_type: str | None = Field(default=None, max_length=80)
    epic_key: str | None = Field(default=None, max_length=50)
    story_points: Decimal = Field(default=Decimal("0"), ge=0, le=10000)
    blocked: bool = False
    blocked_since: datetime | None = None
    flagged: bool = False
    added_to_sprint_at: datetime | None = None
    removed_from_sprint_at: datetime | None = None
    completed_at: datetime | None = None
    source_updated_at: datetime
    normalized_fields: dict[str, Any] = Field(default_factory=dict)


class JiraIssueRead(JiraIssueUpsert, ORMModel):
    id: UUID
    organization_id: UUID


class EmployeeCapacityRead(ORMModel):
    id: UUID
    sprint_id: UUID
    employee_id: UUID
    calculated_at: datetime
    working_days: Decimal
    gross_hours: Decimal
    leave_hours: Decimal
    holiday_hours: Decimal
    ceremony_hours: Decimal
    buffer_hours: Decimal
    net_hours: Decimal
    effective_person_days: Decimal
    assigned_story_points: Decimal
    inputs: dict[str, Any]


class TeamCapacityRead(ORMModel):
    id: UUID
    sprint_id: UUID
    calculated_at: datetime
    available_hours: Decimal
    effective_person_days: Decimal
    leave_impact_hours: Decimal
    story_points_per_effective_day: Decimal | None
    story_point_capacity: Decimal | None
    committed_story_points: Decimal
    added_story_points: Decimal
    removed_story_points: Decimal
    completed_story_points: Decimal
    in_progress_story_points: Decimal
    remaining_story_points: Decimal
    utilization_percent: Decimal | None
    risk_level: str
    inputs_fresh_as_of: datetime | None


class RiskRead(ORMModel):
    id: UUID
    organization_id: UUID
    team_id: UUID
    sprint_id: UUID | None
    risk_type: str
    severity: RiskSeverity
    message: str
    recommendation: str | None
    source: str
    context: dict[str, Any]
    detected_at: datetime
    resolved_at: datetime | None
    acknowledged_at: datetime | None
    acknowledged_by_user_id: UUID | None


class RiskThresholdUpsert(BaseModel):
    team_id: UUID | None = None
    risk_type: str = Field(min_length=1, max_length=80)
    warning_value: Decimal | None = None
    critical_value: Decimal | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class RiskThresholdRead(RiskThresholdUpsert, ORMModel):
    id: UUID
    organization_id: UUID


class JiraFieldMappingUpsert(BaseModel):
    jira_site_id: str = Field(min_length=1, max_length=100)
    logical_field: str = Field(min_length=1, max_length=100)
    jira_field_id: str = Field(min_length=1, max_length=100)
    transformation: dict[str, Any] = Field(default_factory=dict)


class JiraFieldMappingRead(JiraFieldMappingUpsert, ORMModel):
    id: UUID
    organization_id: UUID


class IdentityMappingRead(ORMModel):
    id: UUID
    organization_id: UUID
    employee_id: UUID | None
    jira_account_id: str | None
    payspace_employee_number: str | None
    corporate_email: str | None
    status: str
    match_method: str | None


class IdentityMappingResolve(BaseModel):
    employee_id: UUID
    match_method: str = Field(default="manual", max_length=50)


class IntegrationConfigurationUpsert(BaseModel):
    source: IntegrationSource
    name: str = Field(min_length=1, max_length=120)
    enabled: bool = True
    configuration: dict[str, Any] = Field(default_factory=dict)
    secret_reference: str | None = Field(default=None, max_length=500)


class IntegrationConfigurationRead(IntegrationConfigurationUpsert, ORMModel):
    id: UUID
    organization_id: UUID


class IntegrationRunRead(ORMModel):
    id: UUID
    organization_id: UUID
    source: IntegrationSource
    run_type: str
    status: IntegrationRunStatus
    started_at: datetime
    completed_at: datetime | None
    records_read: int
    records_written: int
    errors_count: int
    error_summary: str | None


class WebhookAccepted(BaseModel):
    event_id: UUID
    status: str = "accepted"
    duplicate: bool = False


class RecalculationRequest(BaseModel):
    sprint_id: UUID
    synchronous: bool = False


class RecalculationResponse(BaseModel):
    sprint_id: UUID
    status: str
    summary: TeamCapacityRead | None = None


class Freshness(BaseModel):
    jira_last_synced_at: datetime | None
    payspace_last_synced_at: datetime | None
    capacity_calculated_at: datetime | None
    stale_sources: list[str] = Field(default_factory=list)


class TeamMemberCapacity(BaseModel):
    employee: EmployeeRead
    membership: MembershipRead
    capacity: EmployeeCapacityRead | None


class TeamDashboardRead(BaseModel):
    team: TeamRead
    sprint: SprintRead
    capacity: TeamCapacityRead | None
    members: list[TeamMemberCapacity]
    issues: list[JiraIssueRead]
    risks: list[RiskRead]
    freshness: Freshness


class EmployeeStoryPointsHistoryRead(BaseModel):
    sprint_id: UUID
    sprint_name: str
    end_at: datetime
    assigned_story_points: Decimal
    completed_story_points: Decimal
    completed_issue_count: int


class EmployeeProfileRead(BaseModel):
    employee: EmployeeRead
    memberships: list[MembershipRead]
    current_capacity: EmployeeCapacityRead | None
    current_issues: list[JiraIssueRead]
    completed_issues: list[JiraIssueRead]
    leave: list[LeaveRead]
    historical_capacity: list[EmployeeCapacityRead]
    story_points_history: list[EmployeeStoryPointsHistoryRead]


class PlannedVsActualRead(BaseModel):
    sprint_id: UUID
    sprint_name: str
    committed_story_points: Decimal
    added_story_points: Decimal
    removed_story_points: Decimal
    completed_story_points: Decimal
    carry_over_story_points: Decimal
    delivery_percent: Decimal | None


class SprintSnapshotRead(ORMModel):
    id: UUID
    sprint_id: UUID
    snapshot_type: str
    captured_at: datetime
    committed_story_points: Decimal
    added_story_points: Decimal
    removed_story_points: Decimal
    completed_story_points: Decimal


class SprintTimelineRead(BaseModel):
    sprint: SprintRead
    snapshots: list[SprintSnapshotRead]
    issues: list[JiraIssueRead]


class CurrentUserRead(BaseModel):
    subject: str
    organization_id: UUID
    user_id: UUID | None
    email: str | None
    roles: list[Role]
    team_ids: list[UUID]
    permissions: list[str]


class HealthRead(BaseModel):
    status: str
    version: str
    environment: str
    database: str | None = None
