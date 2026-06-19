import hashlib
import json
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.core.logging import correlation_id_context
from app.core.security import Principal, Role
from app.domain.capacity import (
    CapacityPolicy,
    EmployeeCapacityInput,
    LeaveWindow,
    calculate_employee_capacity,
    calculate_utilization,
    story_points_per_effective_day,
    working_dates,
)
from app.domain.risks import RiskContext, RiskPolicy, detect_risks
from app.infrastructure.repositories import (
    AdminRepository,
    EmployeeRepository,
    PlanningRepository,
    TeamRepository,
)
from app.models import (
    AuditLog,
    CapacityProfile,
    Employee,
    EmployeeCapacitySnapshot,
    IdentityMapping,
    IntegrationConfiguration,
    JiraFieldMapping,
    JiraIssue,
    LeaveRecord,
    Organization,
    OutboxEvent,
    PublicHoliday,
    RiskSignal,
    RiskThreshold,
    Sprint,
    SprintCommitmentSnapshot,
    Team,
    TeamCapacitySummary,
    TeamMembership,
    WebhookEvent,
)
from app.models.entities import (
    IntegrationSource,
    RiskSeverity,
    SnapshotType,
    SprintState,
)
from app.schemas.contracts import (
    CapacityProfileUpsert,
    EmployeeCreate,
    EmployeeProfileRead,
    EmployeeRead,
    EmployeeStoryPointsHistoryRead,
    Freshness,
    IntegrationConfigurationUpsert,
    JiraFieldMappingUpsert,
    JiraIssueRead,
    JiraIssueUpsert,
    LeaveCreate,
    LeaveRead,
    MembershipCreate,
    MembershipRead,
    PublicHolidayCreate,
    RiskRead,
    RiskThresholdUpsert,
    SprintCreate,
    SprintRead,
    SprintUpdate,
    TeamCapacityRead,
    TeamCreate,
    TeamDashboardRead,
    TeamMemberCapacity,
    TeamRead,
    TeamUpdate,
)

ZERO = Decimal("0")


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def record(
        self,
        principal: Principal,
        action: str,
        resource_type: str,
        resource_id: object | None,
        *,
        team_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.session.add(
            AuditLog(
                organization_id=principal.organization_id,
                actor_subject=principal.subject,
                actor_user_id=principal.user_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                team_id=team_id,
                occurred_at=datetime.now(UTC),
                correlation_id=correlation_id_context.get(),
                metadata_json=metadata or {},
            )
        )


class AuthorizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.employees = EmployeeRepository(session)

    def require_team(self, principal: Principal, team_id: UUID) -> None:
        if not principal.can_access_team(team_id):
            raise AuthorizationError("You are not authorized for this team")

    async def require_employee(self, principal: Principal, employee_id: UUID) -> None:
        if Role.SYSTEM_ADMIN in principal.roles or Role.HR_ADMIN in principal.roles:
            return
        if not await self.employees.can_access_via_team(employee_id, principal.team_ids):
            raise AuthorizationError("You are not authorized for this employee")


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.teams = TeamRepository(session)
        self.employees = EmployeeRepository(session)
        self.planning = PlanningRepository(session)
        self.audit = AuditService(session)

    async def create_organization(self, payload: Any) -> Organization:
        organization = Organization(**payload.model_dump())
        self.session.add(organization)
        await self._commit_unique("Organization slug already exists")
        return organization

    async def create_team(self, principal: Principal, payload: TeamCreate) -> Team:
        team = Team(organization_id=principal.organization_id, **payload.model_dump())
        self.session.add(team)
        await self.session.flush()
        self.audit.record(principal, "team.create", "team", team.id, team_id=team.id)
        await self._commit_unique("A team with this slug already exists")
        return team

    async def update_team(self, principal: Principal, team_id: UUID, payload: TeamUpdate) -> Team:
        team = await self.teams.get(principal.organization_id, team_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(team, key, value)
        self.audit.record(principal, "team.update", "team", team.id, team_id=team.id)
        await self.session.commit()
        await self.session.refresh(team)
        return team

    async def create_employee(self, principal: Principal, payload: EmployeeCreate) -> Employee:
        employee = Employee(organization_id=principal.organization_id, **payload.model_dump())
        self.session.add(employee)
        await self.session.flush()
        self.audit.record(principal, "employee.create", "employee", employee.id)
        await self._commit_unique("An employee with this corporate email already exists")
        return employee

    async def upsert_payspace_employee(
        self, principal: Principal, payload: EmployeeCreate
    ) -> Employee:
        if not payload.payspace_employee_number:
            raise ConflictError(
                "payspace_employee_number is required for PaySpace upsert",
                "missing_source_identifier",
            )
        employee = await self.session.scalar(
            select(Employee).where(
                Employee.organization_id == principal.organization_id,
                Employee.payspace_employee_number == payload.payspace_employee_number,
            )
        )
        if employee is None:
            employee = Employee(organization_id=principal.organization_id, **payload.model_dump())
            self.session.add(employee)
        else:
            for key, value in payload.model_dump().items():
                setattr(employee, key, value)
        employee.source_updated_at = datetime.now(UTC)
        await self.session.flush()
        self._outbox(
            principal.organization_id,
            "employee",
            employee.id,
            "PaySpaceEmployeeUpdated",
            {"employee_id": str(employee.id)},
        )
        await self._commit_unique("PaySpace employee identity conflicts with an existing record")
        return employee

    async def update_employee(
        self, principal: Principal, employee_id: UUID, payload: Any
    ) -> Employee:
        employee = await self.employees.get(principal.organization_id, employee_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(employee, key, value)
        self.audit.record(principal, "employee.update", "employee", employee.id)
        await self._commit_unique("Employee identity conflicts with an existing record")
        return employee

    async def add_membership(
        self, principal: Principal, team_id: UUID, payload: MembershipCreate
    ) -> TeamMembership:
        await self.teams.get(principal.organization_id, team_id)
        await self.employees.get(principal.organization_id, payload.employee_id)
        overlap = await self.session.scalar(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.employee_id == payload.employee_id,
                TeamMembership.start_date <= (payload.end_date or date.max),
                or_(
                    TeamMembership.end_date.is_(None), TeamMembership.end_date >= payload.start_date
                ),
            )
        )
        if overlap:
            raise ConflictError("This employee already has an overlapping team membership")
        membership = TeamMembership(team_id=team_id, **payload.model_dump())
        self.session.add(membership)
        self.audit.record(
            principal,
            "team.membership.create",
            "team_membership",
            membership.id,
            team_id=team_id,
        )
        self._outbox(
            principal.organization_id,
            "team",
            team_id,
            "EmployeeTeamChanged",
            {"employee_id": str(payload.employee_id)},
        )
        await self.session.commit()
        return membership

    async def create_leave(self, principal: Principal, payload: LeaveCreate) -> LeaveRecord:
        employee = await self.employees.get(principal.organization_id, payload.employee_id)
        leave = LeaveRecord(**payload.model_dump())
        self.session.add(leave)
        self.audit.record(principal, "leave.create", "leave", leave.id)
        self._outbox(
            principal.organization_id,
            "employee",
            employee.id,
            "PaySpaceLeaveUpdated",
            {"employee_id": str(employee.id), "start_date": payload.start_date.isoformat()},
        )
        await self._commit_unique("This source leave record has already been imported")
        return leave

    async def upsert_payspace_leave(
        self, principal: Principal, payload: LeaveCreate
    ) -> LeaveRecord:
        await self.employees.get(principal.organization_id, payload.employee_id)
        leave = await self.session.scalar(
            select(LeaveRecord).where(
                LeaveRecord.employee_id == payload.employee_id,
                LeaveRecord.source_reference_id == payload.source_reference_id,
            )
        )
        if leave is None:
            leave = LeaveRecord(**payload.model_dump())
            self.session.add(leave)
        else:
            for key, value in payload.model_dump().items():
                setattr(leave, key, value)
        leave.source_updated_at = datetime.now(UTC)
        await self.session.flush()
        self._outbox(
            principal.organization_id,
            "employee",
            payload.employee_id,
            "PaySpaceLeaveUpdated",
            {"employee_id": str(payload.employee_id)},
        )
        await self.session.commit()
        return leave

    async def create_holiday(
        self, principal: Principal, payload: PublicHolidayCreate
    ) -> PublicHoliday:
        holiday = PublicHoliday(organization_id=principal.organization_id, **payload.model_dump())
        self.session.add(holiday)
        self.audit.record(principal, "holiday.create", "public_holiday", holiday.id)
        await self._commit_unique("This holiday already exists for the location and date")
        return holiday

    async def upsert_profile(
        self, principal: Principal, payload: CapacityProfileUpsert
    ) -> CapacityProfile:
        profile = await self.session.scalar(
            select(CapacityProfile).where(
                CapacityProfile.organization_id == principal.organization_id,
                CapacityProfile.role_name == payload.role_name,
            )
        )
        if profile is None:
            profile = CapacityProfile(
                organization_id=principal.organization_id, **payload.model_dump()
            )
            self.session.add(profile)
        else:
            for key, value in payload.model_dump().items():
                setattr(profile, key, value)
        self.audit.record(principal, "capacity_profile.upsert", "capacity_profile", profile.id)
        await self.session.commit()
        return profile

    async def create_sprint(self, principal: Principal, payload: SprintCreate) -> Sprint:
        await self.teams.get(principal.organization_id, payload.team_id)
        sprint = Sprint(**payload.model_dump())
        self.session.add(sprint)
        await self.session.flush()
        self.audit.record(principal, "sprint.create", "sprint", sprint.id, team_id=payload.team_id)
        await self._commit_unique("This Jira sprint is already mapped to the team")
        return sprint

    async def update_sprint(
        self, principal: Principal, sprint_id: UUID, payload: SprintUpdate
    ) -> Sprint:
        sprint = await self.planning.get_sprint(principal.organization_id, sprint_id)
        previous_state = sprint.state
        values = payload.model_dump(exclude_unset=True)
        start_at = values.get("start_at", sprint.start_at)
        end_at = values.get("end_at", sprint.end_at)
        if _as_utc(end_at) <= _as_utc(start_at):
            raise ConflictError("Sprint end must be after sprint start", "invalid_sprint_dates")
        for key, value in values.items():
            setattr(sprint, key, value)
        self.audit.record(principal, "sprint.update", "sprint", sprint.id, team_id=sprint.team_id)
        if previous_state != SprintState.ACTIVE and sprint.state == SprintState.ACTIVE:
            await self.capture_snapshot(principal, sprint, SnapshotType.START)
            self._outbox(
                principal.organization_id,
                "sprint",
                sprint.id,
                "SprintStarted",
                {"sprint_id": str(sprint.id)},
            )
        await self.session.commit()
        return sprint

    async def capture_sprint_snapshot(
        self, principal: Principal, sprint_id: UUID, snapshot_type: SnapshotType
    ) -> SprintCommitmentSnapshot:
        sprint = await self.planning.get_sprint(principal.organization_id, sprint_id)
        snapshot = await self.capture_snapshot(principal, sprint, snapshot_type)
        self.audit.record(
            principal,
            "sprint.snapshot.create",
            "sprint_snapshot",
            snapshot.id,
            team_id=sprint.team_id,
            metadata={"snapshot_type": snapshot_type.value},
        )
        await self.session.commit()
        return snapshot

    async def capture_snapshot(
        self, principal: Principal, sprint: Sprint, snapshot_type: SnapshotType
    ) -> SprintCommitmentSnapshot:
        issues = await self.planning.issues(
            principal.organization_id, sprint_id=sprint.id, limit=10000
        )
        active = [issue for issue in issues if issue.removed_from_sprint_at is None]
        committed = sum(
            (
                issue.story_points
                for issue in active
                if issue.added_to_sprint_at is None
                or _as_utc(issue.added_to_sprint_at) <= _as_utc(sprint.start_at)
            ),
            start=ZERO,
        )
        added = sum(
            (
                issue.story_points
                for issue in issues
                if issue.added_to_sprint_at
                and _as_utc(issue.added_to_sprint_at) > _as_utc(sprint.start_at)
            ),
            start=ZERO,
        )
        removed = sum(
            (issue.story_points for issue in issues if issue.removed_from_sprint_at), start=ZERO
        )
        completed = sum(
            (issue.story_points for issue in issues if issue.status_category.lower() == "done"),
            start=ZERO,
        )
        snapshot = SprintCommitmentSnapshot(
            sprint_id=sprint.id,
            snapshot_type=snapshot_type,
            captured_at=datetime.now(UTC),
            issue_ids=[issue.external_id for issue in active],
            committed_story_points=committed,
            added_story_points=added,
            removed_story_points=removed,
            completed_story_points=completed,
        )
        self.session.add(snapshot)
        return snapshot

    async def upsert_jira_issue(self, principal: Principal, payload: JiraIssueUpsert) -> JiraIssue:
        if payload.sprint_id:
            sprint = await self.planning.get_sprint(principal.organization_id, payload.sprint_id)
            if (
                not principal.can_access_team(sprint.team_id)
                and Role.SYSTEM_ADMIN not in principal.roles
            ):
                raise AuthorizationError("You are not authorized for the issue's sprint")
        issue = await self.session.scalar(
            select(JiraIssue).where(
                JiraIssue.organization_id == principal.organization_id,
                JiraIssue.jira_site_id == payload.jira_site_id,
                JiraIssue.external_id == payload.external_id,
            )
        )
        if issue is None:
            issue = JiraIssue(organization_id=principal.organization_id, **payload.model_dump())
            self.session.add(issue)
        elif _as_utc(payload.source_updated_at) >= _as_utc(issue.source_updated_at):
            for key, value in payload.model_dump().items():
                setattr(issue, key, value)
        self._outbox(
            principal.organization_id,
            "jira_issue",
            issue.id,
            "JiraIssueUpdated",
            {"external_id": payload.external_id, "sprint_id": str(payload.sprint_id or "")},
        )
        await self.session.commit()
        return issue

    def _outbox(
        self,
        organization_id: UUID,
        aggregate_type: str,
        aggregate_id: UUID | None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        self.session.add(
            OutboxEvent(
                organization_id=organization_id,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload=payload,
                occurred_at=datetime.now(UTC),
            )
        )

    async def _commit_unique(self, message: str) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(message) from exc


class CapacityPlanningService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.teams = TeamRepository(session)
        self.employees = EmployeeRepository(session)
        self.planning = PlanningRepository(session)
        self.admin = AdminRepository(session)

    async def recalculate(self, organization_id: UUID, sprint_id: UUID) -> TeamCapacitySummary:
        now = datetime.now(UTC)
        sprint = await self.planning.get_sprint(organization_id, sprint_id)
        team = await self.teams.get(organization_id, sprint.team_id)
        start, end = sprint.start_at.date(), sprint.end_at.date()
        memberships = await self.teams.effective_memberships(team.id, start, end)
        employees = await self.employees.get_many(
            organization_id, [membership.employee_id for membership in memberships]
        )
        employee_by_id = {employee.id: employee for employee in employees}
        leaves = await self.employees.leaves(list(employee_by_id), start, end)
        leaves_by_employee: dict[UUID, list[LeaveRecord]] = defaultdict(list)
        for leave in leaves:
            leaves_by_employee[leave.employee_id].append(leave)
        holidays = await self.planning.holidays(organization_id, start, end)
        holidays_by_location: dict[str, set[date]] = defaultdict(set)
        for holiday in holidays:
            holidays_by_location[holiday.location_code].add(holiday.holiday_date)
        profiles = {
            profile.role_name.casefold(): profile
            for profile in await self.planning.profiles(organization_id)
        }
        issues = await self.planning.issues(organization_id, sprint_id=sprint.id, limit=10000)
        assigned: dict[UUID, Decimal] = defaultdict(lambda: ZERO)
        for issue in issues:
            if issue.assignee_employee_id and issue.removed_from_sprint_at is None:
                assigned[issue.assignee_employee_id] += issue.story_points

        total_net = ZERO
        total_gross = ZERO
        total_leave = ZERO
        total_days = ZERO
        critical_absence = ZERO
        for membership in memberships:
            employee = employee_by_id.get(membership.employee_id)
            if employee is None or not employee.active:
                continue
            profile = profiles.get(employee.role_name.casefold())
            capacity_policy = CapacityPolicy(
                ceremony_hours_per_sprint=(profile.ceremony_hours_per_sprint if profile else ZERO),
                meeting_buffer_percent=(
                    profile.meeting_buffer_percent if profile else Decimal("10")
                ),
                support_buffer_percent=(
                    profile.support_buffer_percent if profile else Decimal("5")
                ),
                review_buffer_percent=(profile.review_buffer_percent if profile else Decimal("5")),
                unplanned_buffer_percent=(
                    profile.unplanned_buffer_percent if profile else Decimal("10")
                ),
            )
            location = employee.location_code or team.location_code or "DEFAULT"
            result = calculate_employee_capacity(
                EmployeeCapacityInput(
                    sprint_start=start,
                    sprint_end=end,
                    contract_hours_per_day=employee.contract_hours_per_day,
                    fte_factor=employee.fte_factor,
                    allocation_percent=membership.allocation_percent,
                    holidays=frozenset(holidays_by_location.get(location, set())),
                    leave=tuple(
                        LeaveWindow(item.start_date, item.end_date, item.partial_day_hours)
                        for item in leaves_by_employee[employee.id]
                    ),
                    policy=capacity_policy,
                )
            )
            snapshot = await self.session.scalar(
                select(EmployeeCapacitySnapshot).where(
                    EmployeeCapacitySnapshot.sprint_id == sprint.id,
                    EmployeeCapacitySnapshot.employee_id == employee.id,
                )
            )
            values = {
                "calculated_at": now,
                "working_days": result.working_days,
                "gross_hours": result.gross_hours,
                "leave_hours": result.leave_hours,
                "holiday_hours": result.holiday_hours,
                "ceremony_hours": result.ceremony_hours,
                "buffer_hours": result.buffer_hours,
                "net_hours": result.net_hours,
                "effective_person_days": result.effective_person_days,
                "assigned_story_points": assigned[employee.id],
                "inputs": {
                    "role": employee.role_name,
                    "allocation_percent": str(membership.allocation_percent),
                    "fte_factor": str(employee.fte_factor),
                    "location_code": location,
                },
            }
            if snapshot is None:
                snapshot = EmployeeCapacitySnapshot(
                    sprint_id=sprint.id, employee_id=employee.id, **values
                )
                self.session.add(snapshot)
            else:
                for key, value in values.items():
                    setattr(snapshot, key, value)
            total_net += result.net_hours
            total_gross += result.gross_hours
            total_leave += result.leave_hours
            total_days += result.effective_person_days
            if membership.critical_role and result.gross_hours > ZERO:
                critical_absence = max(
                    critical_absence,
                    result.leave_hours / result.gross_hours * Decimal("100"),
                )

        sprint_start_at = _as_utc(sprint.start_at)
        history = await self.planning.velocity_history(
            team.id, sprint.start_at, team.velocity_lookback
        )
        sp_per_day = story_points_per_effective_day(
            [(item.completed_story_points, item.effective_person_days) for item in history]
        )
        sp_capacity = (
            (total_days * sp_per_day).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if sp_per_day is not None
            else None
        )
        start_snapshot = await self.planning.start_snapshot(sprint.id)
        committed = (
            start_snapshot.committed_story_points
            if start_snapshot
            else sum(
                (
                    issue.story_points
                    for issue in issues
                    if issue.added_to_sprint_at is None
                    or _as_utc(issue.added_to_sprint_at) <= sprint_start_at
                ),
                start=ZERO,
            )
        )
        added = sum(
            (
                issue.story_points
                for issue in issues
                if issue.added_to_sprint_at and _as_utc(issue.added_to_sprint_at) > sprint_start_at
            ),
            start=ZERO,
        )
        removed = sum(
            (issue.story_points for issue in issues if issue.removed_from_sprint_at), start=ZERO
        )
        completed = sum(
            (issue.story_points for issue in issues if issue.status_category.casefold() == "done"),
            start=ZERO,
        )
        in_progress = sum(
            (
                issue.story_points
                for issue in issues
                if issue.status_category.casefold() in {"in progress", "indeterminate"}
                and issue.removed_from_sprint_at is None
            ),
            start=ZERO,
        )
        current_load = max(ZERO, committed + added - removed)
        remaining = max(ZERO, current_load - completed)
        utilization = calculate_utilization(current_load, sp_capacity)
        runs = await self.admin.latest_successful_runs(organization_id)
        run_times = [_as_utc(run.completed_at) for run in runs.values() if run.completed_at]
        fresh_as_of = min(run_times) if run_times else None
        stale_hours = (
            Decimal(str((now - fresh_as_of).total_seconds() / 3600)).quantize(Decimal("0.1"))
            if fresh_as_of
            else Decimal("999")
        )

        summary = await self.planning.summary(sprint.id)
        values_summary = {
            "calculated_at": now,
            "available_hours": total_net.quantize(Decimal("0.01")),
            "effective_person_days": total_days.quantize(Decimal("0.001")),
            "leave_impact_hours": total_leave.quantize(Decimal("0.01")),
            "story_points_per_effective_day": sp_per_day,
            "story_point_capacity": sp_capacity,
            "committed_story_points": committed,
            "added_story_points": added,
            "removed_story_points": removed,
            "completed_story_points": completed,
            "in_progress_story_points": in_progress,
            "remaining_story_points": remaining,
            "utilization_percent": utilization,
            "risk_level": "unknown",
            "inputs_fresh_as_of": fresh_as_of,
        }
        if summary is None:
            summary = TeamCapacitySummary(sprint_id=sprint.id, **values_summary)
            self.session.add(summary)
        else:
            for key, value in values_summary.items():
                setattr(summary, key, value)
        await self.session.flush()

        risk_context = await self._risk_context(
            organization_id=organization_id,
            sprint=sprint,
            issues=issues,
            committed=committed,
            added=added,
            current_load=current_load,
            total_gross=total_gross,
            total_leave=total_leave,
            critical_absence=critical_absence,
            utilization=utilization,
            stale_hours=stale_hours,
            holidays={item.holiday_date for item in holidays},
        )
        risk_policy = await self._risk_policy(organization_id, team.id)
        domain_risks = detect_risks(risk_context, risk_policy)
        severities = await self._persist_risks(
            organization_id, team.id, sprint.id, domain_risks, now
        )
        rank = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        summary.risk_level = max(severities, key=lambda value: rank[value], default="healthy")
        await self.session.commit()
        await self.session.refresh(summary)
        return summary

    async def _risk_context(
        self,
        *,
        organization_id: UUID,
        sprint: Sprint,
        issues: list[JiraIssue],
        committed: Decimal,
        added: Decimal,
        current_load: Decimal,
        total_gross: Decimal,
        total_leave: Decimal,
        critical_absence: Decimal,
        utilization: Decimal | None,
        stale_hours: Decimal,
        holidays: set[date],
    ) -> RiskContext:
        now = datetime.now(UTC)
        sprint_start = _as_utc(sprint.start_at)
        sprint_end = _as_utc(sprint.end_at)
        duration = max((sprint_end - sprint_start).total_seconds(), 1)
        progress = Decimal(str((now - sprint_start).total_seconds() / duration * 100))
        progress = min(Decimal("100"), max(ZERO, progress)).quantize(Decimal("0.1"))
        not_started = sum(
            (
                issue.story_points
                for issue in issues
                if issue.status_category.casefold() in {"to do", "new"}
                and issue.removed_from_sprint_at is None
            ),
            start=ZERO,
        )
        blocked = 0
        for issue in issues:
            if issue.blocked and issue.blocked_since:
                days = working_dates(issue.blocked_since.date(), now.date(), holidays)
                if len(days) > 2:
                    blocked += 1
        high_priorities = {"highest", "high", "critical", "blocker"}
        unassigned = sum(
            1
            for issue in issues
            if issue.assignee_employee_id is None
            and (issue.priority or "").casefold() in high_priorities
            and issue.removed_from_sprint_at is None
        )
        unresolved = len(await self.admin.unresolved_mappings(organization_id))
        previous = await self.session.scalars(
            select(TeamCapacitySummary)
            .join(Sprint, Sprint.id == TeamCapacitySummary.sprint_id)
            .where(Sprint.team_id == sprint.team_id, Sprint.end_at < sprint.start_at)
            .order_by(Sprint.end_at.desc())
            .limit(3)
        )
        previous_list = list(previous)
        carry_over = 0
        for item in previous_list:
            if item.remaining_story_points > ZERO:
                carry_over += 1
            else:
                break
        return RiskContext(
            utilization_percent=utilization,
            leave_impact_percent=(
                (total_leave / total_gross * Decimal("100")).quantize(Decimal("0.1"))
                if total_gross > ZERO
                else ZERO
            ),
            critical_role_unavailable_percent=critical_absence.quantize(Decimal("0.1")),
            added_scope_percent=(
                (added / committed * Decimal("100")).quantize(Decimal("0.1"))
                if committed > ZERO
                else ZERO
            ),
            not_started_percent=(
                (not_started / current_load * Decimal("100")).quantize(Decimal("0.1"))
                if current_load > ZERO
                else ZERO
            ),
            sprint_progress_percent=progress,
            blocked_issues_over_threshold=blocked,
            unassigned_high_priority_issues=unassigned,
            stale_data_hours=stale_hours,
            recurring_carry_over_sprints=carry_over,
            unresolved_mappings=unresolved,
        )

    async def _risk_policy(self, organization_id: UUID, team_id: UUID) -> RiskPolicy:
        values: dict[str, Any] = {}
        for threshold in await self.admin.thresholds(organization_id, team_id):
            if threshold.warning_value is not None:
                values[f"{threshold.risk_type}:warning"] = threshold.warning_value
            if threshold.critical_value is not None:
                values[f"{threshold.risk_type}:critical"] = threshold.critical_value
            values.update(
                {f"{threshold.risk_type}:{k}": v for k, v in threshold.configuration.items()}
            )
        return RiskPolicy(
            under_capacity_percent=Decimal(values.get("UTILIZATION:under", "70")),
            watch_capacity_percent=Decimal(values.get("UTILIZATION:warning", "95")),
            over_capacity_percent=Decimal(values.get("UTILIZATION:critical", "110")),
            critical_role_unavailable_percent=Decimal(
                values.get("CRITICAL_ROLE_UNAVAILABLE:critical", "25")
            ),
            scope_change_percent=Decimal(values.get("SCOPE_CREEP:critical", "20")),
            not_started_percent=Decimal(values.get("LOW_COMPLETION_PROBABILITY:critical", "30")),
            blocked_working_days=int(values.get("BLOCKED_WORK:days", 2)),
            stale_data_hours=int(values.get("DATA_STALENESS:hours", 8)),
        )

    async def _persist_risks(
        self,
        organization_id: UUID,
        team_id: UUID,
        sprint_id: UUID,
        risks: list[Any],
        now: datetime,
    ) -> list[str]:
        existing = await self.planning.risks(
            organization_id, team_id=team_id, sprint_id=sprint_id, active_only=True
        )
        by_type = {item.risk_type: item for item in existing}
        active_types: set[str] = set()
        severities: list[str] = []
        for risk in risks:
            risk_type = risk.risk_type.value
            active_types.add(risk_type)
            severities.append(risk.severity.value)
            signal = by_type.get(risk_type)
            if signal is None:
                signal = RiskSignal(
                    organization_id=organization_id,
                    team_id=team_id,
                    sprint_id=sprint_id,
                    risk_type=risk_type,
                    severity=RiskSeverity(risk.severity.value),
                    message=risk.message,
                    recommendation=risk.recommendation,
                    source="CAPACITY_ENGINE",
                    fingerprint=risk.fingerprint,
                    context=risk.context,
                    detected_at=now,
                )
                self.session.add(signal)
            else:
                signal.severity = RiskSeverity(risk.severity.value)
                signal.message = risk.message
                signal.recommendation = risk.recommendation
                signal.fingerprint = risk.fingerprint
                signal.context = risk.context
        for signal in existing:
            if signal.risk_type not in active_types:
                signal.resolved_at = now
        return severities


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.teams = TeamRepository(session)
        self.employees = EmployeeRepository(session)
        self.planning = PlanningRepository(session)
        self.admin = AdminRepository(session)
        self.audit = AuditService(session)

    async def team_dashboard(
        self, principal: Principal, team_id: UUID, sprint_id: UUID
    ) -> TeamDashboardRead:
        team = await self.teams.get(principal.organization_id, team_id)
        sprint = await self.planning.get_sprint(principal.organization_id, sprint_id)
        if sprint.team_id != team.id:
            raise NotFoundError("Sprint", sprint_id)
        memberships = await self.teams.effective_memberships(
            team.id, sprint.start_at.date(), sprint.end_at.date()
        )
        employees = await self.employees.get_many(
            principal.organization_id, [item.employee_id for item in memberships]
        )
        snapshots = {
            item.employee_id: item for item in await self.planning.employee_snapshots(sprint.id)
        }
        member_by_employee = {item.employee_id: item for item in memberships}
        issues = await self.planning.issues(
            principal.organization_id, sprint_id=sprint.id, limit=10000
        )
        risks = await self.planning.risks(
            principal.organization_id, team_id=team.id, sprint_id=sprint.id
        )
        summary = await self.planning.summary(sprint.id)
        freshness = await self._freshness(principal.organization_id, summary)
        self.audit.record(principal, "team.dashboard.read", "team", team.id, team_id=team.id)
        await self.session.commit()
        return TeamDashboardRead(
            team=TeamRead.model_validate(team),
            sprint=SprintRead.model_validate(sprint),
            capacity=TeamCapacityRead.model_validate(summary) if summary else None,
            members=[
                TeamMemberCapacity(
                    employee=EmployeeRead.model_validate(employee),
                    membership=MembershipRead.model_validate(member_by_employee[employee.id]),
                    capacity=snapshots.get(employee.id),
                )
                for employee in employees
            ],
            issues=[JiraIssueRead.model_validate(issue) for issue in issues],
            risks=[RiskRead.model_validate(risk) for risk in risks],
            freshness=freshness,
        )

    async def employee_profile(
        self, principal: Principal, employee_id: UUID, include_leave_reason: bool
    ) -> EmployeeProfileRead:
        employee = await self.employees.get(principal.organization_id, employee_id)
        memberships = await self.employees.memberships(employee.id)
        current_sprint = await self.session.scalar(
            select(Sprint)
            .join(TeamMembership, TeamMembership.team_id == Sprint.team_id)
            .where(
                TeamMembership.employee_id == employee.id,
                Sprint.state == SprintState.ACTIVE,
            )
            .order_by(Sprint.start_at.desc())
            .limit(1)
        )
        current_capacity = None
        if current_sprint:
            snapshots = await self.planning.employee_snapshots(current_sprint.id, employee.id)
            current_capacity = snapshots[0] if snapshots else None
        current_issues = (
            await self.planning.issues(
                principal.organization_id,
                sprint_id=current_sprint.id,
                employee_id=employee.id,
                limit=1000,
            )
            if current_sprint
            else []
        )
        completed_issues = await self.planning.issues(
            principal.organization_id,
            employee_id=employee.id,
            status_category="Done",
            limit=50,
        )
        today = date.today()
        leaves = await self.employees.leaves(
            [employee.id], date(today.year - 1, 1, 1), date(today.year + 1, 12, 31)
        )
        leave_models: list[LeaveRead] = []
        for leave in leaves:
            model = LeaveRead.model_validate(leave)
            if not include_leave_reason:
                model.reason = None
            leave_models.append(model)
        historical = await self.planning.historical_employee_snapshots(employee.id)
        story_points_history = await self.planning.employee_story_points_history(employee.id)
        self.audit.record(
            principal,
            "employee.profile.read",
            "employee",
            employee.id,
            metadata={"leave_reason_included": include_leave_reason},
        )
        await self.session.commit()
        return EmployeeProfileRead(
            employee=EmployeeRead.model_validate(employee),
            memberships=[MembershipRead.model_validate(item) for item in memberships],
            current_capacity=current_capacity,
            current_issues=[JiraIssueRead.model_validate(item) for item in current_issues],
            completed_issues=[JiraIssueRead.model_validate(item) for item in completed_issues],
            leave=leave_models,
            historical_capacity=historical,
            story_points_history=[
                EmployeeStoryPointsHistoryRead(
                    sprint_id=sprint.id,
                    sprint_name=sprint.name,
                    end_at=sprint.end_at,
                    assigned_story_points=assigned,
                    completed_story_points=completed,
                    completed_issue_count=completed_count,
                )
                for sprint, assigned, completed, completed_count in story_points_history
            ],
        )

    async def _freshness(
        self, organization_id: UUID, summary: TeamCapacitySummary | None
    ) -> Freshness:
        runs = await self.admin.latest_successful_runs(organization_id)
        jira = runs.get(IntegrationSource.JIRA)
        payspace = runs.get(IntegrationSource.PAYSPACE)
        now = datetime.now(UTC)
        stale: list[str] = []
        for source, run in (("jira", jira), ("payspace", payspace)):
            if (
                run is None
                or run.completed_at is None
                or (now - _as_utc(run.completed_at)).total_seconds() > 8 * 3600
            ):
                stale.append(source)
        return Freshness(
            jira_last_synced_at=jira.completed_at if jira else None,
            payspace_last_synced_at=payspace.completed_at if payspace else None,
            capacity_calculated_at=summary.calculated_at if summary else None,
            stale_sources=stale,
        )


class RiskManagementService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditService(session)

    async def acknowledge(self, principal: Principal, team_id: UUID, risk_id: UUID) -> RiskSignal:
        risk = await self.session.scalar(
            select(RiskSignal).where(
                RiskSignal.id == risk_id,
                RiskSignal.team_id == team_id,
                RiskSignal.organization_id == principal.organization_id,
                RiskSignal.resolved_at.is_(None),
            )
        )
        if risk is None:
            raise NotFoundError("Active risk", risk_id)
        risk.acknowledged_at = datetime.now(UTC)
        risk.acknowledged_by_user_id = principal.user_id
        self.audit.record(
            principal,
            "risk.acknowledge",
            "risk_signal",
            risk.id,
            team_id=team_id,
        )
        await self.session.commit()
        return risk


class IntegrationService:
    SENSITIVE_KEYS = {"reason", "comment", "medical_notes", "salary", "identity_document"}

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def accept_webhook(
        self,
        organization_id: UUID,
        source: IntegrationSource,
        external_event_id: str,
        event_type: str,
        body: bytes,
    ) -> tuple[WebhookEvent, bool]:
        organization = await self.session.get(Organization, organization_id)
        if organization is None or not organization.active:
            raise NotFoundError("Organization", organization_id)
        existing = await self.session.scalar(
            select(WebhookEvent).where(
                WebhookEvent.organization_id == organization_id,
                WebhookEvent.source == source,
                WebhookEvent.external_event_id == external_event_id,
            )
        )
        if existing:
            return existing, True
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ConflictError(
                "Webhook body must contain valid JSON", "invalid_webhook_payload"
            ) from exc
        if not isinstance(payload, dict):
            raise ConflictError("Webhook payload must be a JSON object", "invalid_webhook_payload")
        event = WebhookEvent(
            organization_id=organization_id,
            source=source,
            external_event_id=external_event_id,
            event_type=event_type,
            payload_hash=hashlib.sha256(body).hexdigest(),
            normalized_payload=self._sanitize(payload),
            received_at=datetime.now(UTC),
        )
        self.session.add(event)
        await self.session.flush()
        self.session.add(
            OutboxEvent(
                organization_id=organization_id,
                aggregate_type="webhook_event",
                aggregate_id=event.id,
                event_type=f"{source.value.title()}WebhookReceived",
                payload={"webhook_event_id": str(event.id)},
                occurred_at=datetime.now(UTC),
            )
        )
        await self.session.commit()
        return event, False

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: self._sanitize(item)
                for key, item in value.items()
                if key.casefold() not in self.SENSITIVE_KEYS
            }
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return value


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditService(session)

    async def upsert_field_mapping(
        self, principal: Principal, payload: JiraFieldMappingUpsert
    ) -> JiraFieldMapping:
        item = await self.session.scalar(
            select(JiraFieldMapping).where(
                JiraFieldMapping.organization_id == principal.organization_id,
                JiraFieldMapping.jira_site_id == payload.jira_site_id,
                JiraFieldMapping.logical_field == payload.logical_field,
            )
        )
        if item is None:
            item = JiraFieldMapping(
                organization_id=principal.organization_id, **payload.model_dump()
            )
            self.session.add(item)
        else:
            for key, value in payload.model_dump().items():
                setattr(item, key, value)
        self.audit.record(principal, "jira_field_mapping.upsert", "jira_field_mapping", item.id)
        await self.session.commit()
        return item

    async def resolve_identity(
        self, principal: Principal, mapping_id: UUID, employee_id: UUID, match_method: str
    ) -> IdentityMapping:
        item = await self.session.scalar(
            select(IdentityMapping).where(
                IdentityMapping.id == mapping_id,
                IdentityMapping.organization_id == principal.organization_id,
            )
        )
        if item is None:
            raise NotFoundError("Identity mapping", mapping_id)
        employee = await self.session.scalar(
            select(Employee).where(
                Employee.id == employee_id, Employee.organization_id == principal.organization_id
            )
        )
        if employee is None:
            raise NotFoundError("Employee", employee_id)
        item.employee_id = employee_id
        item.status = "verified"
        item.match_method = match_method
        item.verified_by_user_id = principal.user_id
        self.audit.record(principal, "identity_mapping.resolve", "identity_mapping", item.id)
        await self.session.commit()
        return item

    async def upsert_threshold(
        self, principal: Principal, payload: RiskThresholdUpsert
    ) -> RiskThreshold:
        if payload.team_id:
            await TeamRepository(self.session).get(principal.organization_id, payload.team_id)
        item = await self.session.scalar(
            select(RiskThreshold).where(
                RiskThreshold.organization_id == principal.organization_id,
                RiskThreshold.team_id == payload.team_id,
                RiskThreshold.risk_type == payload.risk_type,
            )
        )
        if item is None:
            item = RiskThreshold(organization_id=principal.organization_id, **payload.model_dump())
            self.session.add(item)
        else:
            for key, value in payload.model_dump().items():
                setattr(item, key, value)
        self.audit.record(principal, "risk_threshold.upsert", "risk_threshold", item.id)
        await self.session.commit()
        return item

    async def upsert_integration_configuration(
        self, principal: Principal, payload: IntegrationConfigurationUpsert
    ) -> IntegrationConfiguration:
        item = await self.session.scalar(
            select(IntegrationConfiguration).where(
                IntegrationConfiguration.organization_id == principal.organization_id,
                IntegrationConfiguration.source == payload.source,
                IntegrationConfiguration.name == payload.name,
            )
        )
        if item is None:
            item = IntegrationConfiguration(
                organization_id=principal.organization_id, **payload.model_dump()
            )
            self.session.add(item)
        else:
            for key, value in payload.model_dump().items():
                setattr(item, key, value)
        self.audit.record(principal, "integration_configuration.upsert", "integration", item.id)
        await self.session.commit()
        return item
