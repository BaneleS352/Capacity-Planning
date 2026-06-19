from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Select, case, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import (
    CapacityProfile,
    Employee,
    EmployeeCapacitySnapshot,
    IdentityMapping,
    IntegrationConfiguration,
    IntegrationRun,
    JiraFieldMapping,
    JiraIssue,
    LeaveRecord,
    Organization,
    PublicHoliday,
    RiskSignal,
    RiskThreshold,
    Sprint,
    SprintCommitmentSnapshot,
    Team,
    TeamCapacitySummary,
    TeamMembership,
    TeamVelocityMetric,
)
from app.models.entities import IntegrationRunStatus, IntegrationSource, SnapshotType, SprintState


class TeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, organization_id: UUID, team_id: UUID) -> Team:
        team = await self.session.scalar(
            select(Team).where(Team.id == team_id, Team.organization_id == organization_id)
        )
        if team is None:
            raise NotFoundError("Team", team_id)
        return team

    async def list_page(
        self,
        organization_id: UUID,
        *,
        offset: int,
        limit: int,
        search: str | None,
        department: str | None,
        active: bool | None,
        allowed_team_ids: frozenset[UUID] | None,
        sort: str,
    ) -> tuple[list[Team], int]:
        filters = [Team.organization_id == organization_id]
        if search:
            filters.append(Team.name.ilike(f"%{search}%"))
        if department:
            filters.append(Team.department == department)
        if active is not None:
            filters.append(Team.active == active)
        if allowed_team_ids is not None:
            if not allowed_team_ids:
                return [], 0
            filters.append(Team.id.in_(allowed_team_ids))
        sort_fields = {
            "name": Team.name.asc(),
            "-name": Team.name.desc(),
            "created_at": Team.created_at.asc(),
            "-created_at": Team.created_at.desc(),
        }
        order: Any = sort_fields.get(sort, Team.name.asc())
        total = await self.session.scalar(select(func.count()).select_from(Team).where(*filters))
        rows = await self.session.scalars(
            select(Team).where(*filters).order_by(order, Team.id).offset(offset).limit(limit)
        )
        return list(rows), int(total or 0)

    async def effective_memberships(
        self, team_id: UUID, start: date, end: date
    ) -> list[TeamMembership]:
        rows = await self.session.scalars(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.start_date <= end,
                or_(TeamMembership.end_date.is_(None), TeamMembership.end_date >= start),
            )
        )
        return list(rows)


class EmployeeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, organization_id: UUID, employee_id: UUID) -> Employee:
        employee = await self.session.scalar(
            select(Employee).where(
                Employee.id == employee_id, Employee.organization_id == organization_id
            )
        )
        if employee is None:
            raise NotFoundError("Employee", employee_id)
        return employee

    async def get_many(self, organization_id: UUID, ids: Sequence[UUID]) -> list[Employee]:
        if not ids:
            return []
        rows = await self.session.scalars(
            select(Employee).where(
                Employee.organization_id == organization_id, Employee.id.in_(ids)
            )
        )
        return list(rows)

    async def list_page(
        self,
        organization_id: UUID,
        *,
        offset: int,
        limit: int,
        search: str | None,
        role_name: str | None,
        active: bool | None,
        allowed_team_ids: frozenset[UUID] | None,
        sort: str,
    ) -> tuple[list[Employee], int]:
        filters = [Employee.organization_id == organization_id]
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(Employee.full_name.ilike(pattern), Employee.corporate_email.ilike(pattern))
            )
        if role_name:
            filters.append(Employee.role_name == role_name)
        if active is not None:
            filters.append(Employee.active == active)

        query: Select[tuple[Employee]] = select(Employee).where(*filters)
        count_query = select(func.count(func.distinct(Employee.id))).where(*filters)
        if allowed_team_ids is not None:
            if not allowed_team_ids:
                return [], 0
            query = query.join(TeamMembership).where(TeamMembership.team_id.in_(allowed_team_ids))
            count_query = count_query.join(TeamMembership).where(
                TeamMembership.team_id.in_(allowed_team_ids)
            )
        sort_fields = {
            "name": Employee.full_name.asc(),
            "-name": Employee.full_name.desc(),
            "role": Employee.role_name.asc(),
            "-role": Employee.role_name.desc(),
        }
        total = await self.session.scalar(count_query)
        rows = await self.session.scalars(
            query.distinct()
            .order_by(sort_fields.get(sort, Employee.full_name.asc()), Employee.id)
            .offset(offset)
            .limit(limit)
        )
        return list(rows), int(total or 0)

    async def memberships(self, employee_id: UUID) -> list[TeamMembership]:
        rows = await self.session.scalars(
            select(TeamMembership)
            .where(TeamMembership.employee_id == employee_id)
            .order_by(TeamMembership.start_date.desc())
        )
        return list(rows)

    async def leaves(
        self, employee_ids: Sequence[UUID], start: date, end: date
    ) -> list[LeaveRecord]:
        if not employee_ids:
            return []
        rows = await self.session.scalars(
            select(LeaveRecord).where(
                LeaveRecord.employee_id.in_(employee_ids),
                LeaveRecord.start_date <= end,
                LeaveRecord.end_date >= start,
                LeaveRecord.status == "approved",
            )
        )
        return list(rows)

    async def can_access_via_team(
        self, employee_id: UUID, allowed_team_ids: frozenset[UUID]
    ) -> bool:
        if not allowed_team_ids:
            return False
        value = await self.session.scalar(
            select(func.count())
            .select_from(TeamMembership)
            .where(
                TeamMembership.employee_id == employee_id,
                TeamMembership.team_id.in_(allowed_team_ids),
            )
        )
        return bool(value)


class PlanningRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_sprint(self, organization_id: UUID, sprint_id: UUID) -> Sprint:
        sprint = await self.session.scalar(
            select(Sprint)
            .join(Team, Team.id == Sprint.team_id)
            .where(Sprint.id == sprint_id, Team.organization_id == organization_id)
        )
        if sprint is None:
            raise NotFoundError("Sprint", sprint_id)
        return sprint

    async def list_sprints(
        self,
        organization_id: UUID,
        *,
        team_id: UUID | None,
        state: SprintState | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Sprint], int]:
        filters = [Team.organization_id == organization_id]
        if team_id:
            filters.append(Sprint.team_id == team_id)
        if state:
            filters.append(Sprint.state == state)
        base = select(Sprint).join(Team, Team.id == Sprint.team_id).where(*filters)
        total = await self.session.scalar(
            select(func.count())
            .select_from(Sprint)
            .join(Team, Team.id == Sprint.team_id)
            .where(*filters)
        )
        rows = await self.session.scalars(
            base.order_by(Sprint.start_at.desc(), Sprint.id).offset(offset).limit(limit)
        )
        return list(rows), int(total or 0)

    async def issues(
        self,
        organization_id: UUID,
        *,
        sprint_id: UUID | None = None,
        employee_id: UUID | None = None,
        status_category: str | None = None,
        blocked: bool | None = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> list[JiraIssue]:
        filters = [JiraIssue.organization_id == organization_id]
        if sprint_id:
            filters.append(JiraIssue.sprint_id == sprint_id)
        if employee_id:
            filters.append(JiraIssue.assignee_employee_id == employee_id)
        if status_category:
            filters.append(JiraIssue.status_category == status_category)
        if blocked is not None:
            filters.append(JiraIssue.blocked == blocked)
        rows = await self.session.scalars(
            select(JiraIssue)
            .where(*filters)
            .order_by(JiraIssue.priority.desc(), JiraIssue.issue_key)
            .offset(offset)
            .limit(limit)
        )
        return list(rows)

    async def start_snapshot(self, sprint_id: UUID) -> SprintCommitmentSnapshot | None:
        rows = await self.session.scalars(
            select(SprintCommitmentSnapshot)
            .where(
                SprintCommitmentSnapshot.sprint_id == sprint_id,
                SprintCommitmentSnapshot.snapshot_type == SnapshotType.START,
            )
            .order_by(SprintCommitmentSnapshot.captured_at.asc())
            .limit(1)
        )
        return rows.first()

    async def velocity_history(
        self, team_id: UUID, before: datetime, limit: int
    ) -> list[TeamVelocityMetric]:
        rows = await self.session.scalars(
            select(TeamVelocityMetric)
            .join(Sprint, Sprint.id == TeamVelocityMetric.sprint_id)
            .where(TeamVelocityMetric.team_id == team_id, Sprint.end_at < before)
            .order_by(Sprint.end_at.desc())
            .limit(limit)
        )
        return list(rows)

    async def employee_snapshots(
        self, sprint_id: UUID, employee_id: UUID | None = None
    ) -> list[EmployeeCapacitySnapshot]:
        filters = [EmployeeCapacitySnapshot.sprint_id == sprint_id]
        if employee_id:
            filters.append(EmployeeCapacitySnapshot.employee_id == employee_id)
        rows = await self.session.scalars(select(EmployeeCapacitySnapshot).where(*filters))
        return list(rows)

    async def historical_employee_snapshots(
        self, employee_id: UUID, limit: int = 20
    ) -> list[EmployeeCapacitySnapshot]:
        rows = await self.session.scalars(
            select(EmployeeCapacitySnapshot)
            .where(EmployeeCapacitySnapshot.employee_id == employee_id)
            .order_by(EmployeeCapacitySnapshot.calculated_at.desc())
            .limit(limit)
        )
        return list(rows)

    async def employee_story_points_history(
        self, employee_id: UUID, limit: int = 12
    ) -> list[tuple[Sprint, Decimal, Decimal, int]]:
        completed_filter = or_(
            JiraIssue.completed_at.is_not(None), JiraIssue.status_category == "Done"
        )
        completed_points = (
            select(
                func.coalesce(
                    func.sum(case((completed_filter, JiraIssue.story_points), else_=0)), 0
                )
            )
            .where(
                JiraIssue.sprint_id == Sprint.id,
                JiraIssue.assignee_employee_id == employee_id,
            )
            .correlate(Sprint)
            .scalar_subquery()
        )
        completed_count = (
            select(func.count())
            .select_from(JiraIssue)
            .where(
                JiraIssue.sprint_id == Sprint.id,
                JiraIssue.assignee_employee_id == employee_id,
                completed_filter,
            )
            .correlate(Sprint)
            .scalar_subquery()
        )
        rows = await self.session.execute(
            select(
                Sprint,
                EmployeeCapacitySnapshot.assigned_story_points,
                completed_points,
                completed_count,
            )
            .join(EmployeeCapacitySnapshot, EmployeeCapacitySnapshot.sprint_id == Sprint.id)
            .where(EmployeeCapacitySnapshot.employee_id == employee_id)
            .order_by(Sprint.end_at.desc())
            .limit(limit)
        )
        return [
            (sprint, assigned, Decimal(completed), int(issue_count))
            for sprint, assigned, completed, issue_count in rows
        ]

    async def summary(self, sprint_id: UUID) -> TeamCapacitySummary | None:
        rows = await self.session.scalars(
            select(TeamCapacitySummary).where(TeamCapacitySummary.sprint_id == sprint_id)
        )
        return rows.first()

    async def holidays(self, organization_id: UUID, start: date, end: date) -> list[PublicHoliday]:
        rows = await self.session.scalars(
            select(PublicHoliday).where(
                PublicHoliday.organization_id == organization_id,
                PublicHoliday.holiday_date >= start,
                PublicHoliday.holiday_date <= end,
            )
        )
        return list(rows)

    async def profiles(self, organization_id: UUID) -> list[CapacityProfile]:
        rows = await self.session.scalars(
            select(CapacityProfile).where(
                CapacityProfile.organization_id == organization_id,
                CapacityProfile.active == true(),
            )
        )
        return list(rows)

    async def risks(
        self,
        organization_id: UUID,
        *,
        team_id: UUID | None = None,
        sprint_id: UUID | None = None,
        active_only: bool = True,
    ) -> list[RiskSignal]:
        filters = [RiskSignal.organization_id == organization_id]
        if team_id:
            filters.append(RiskSignal.team_id == team_id)
        if sprint_id:
            filters.append(RiskSignal.sprint_id == sprint_id)
        if active_only:
            filters.append(RiskSignal.resolved_at.is_(None))
        rows = await self.session.scalars(
            select(RiskSignal)
            .where(*filters)
            .order_by(RiskSignal.detected_at.desc(), RiskSignal.id)
        )
        return list(rows)


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def organization(self, organization_id: UUID) -> Organization:
        organization = await self.session.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError("Organization", organization_id)
        return organization

    async def thresholds(self, organization_id: UUID, team_id: UUID | None) -> list[RiskThreshold]:
        rows = await self.session.scalars(
            select(RiskThreshold).where(
                RiskThreshold.organization_id == organization_id,
                RiskThreshold.active == true(),
                or_(RiskThreshold.team_id == team_id, RiskThreshold.team_id.is_(None)),
            )
        )
        return list(rows)

    async def unresolved_mappings(self, organization_id: UUID) -> list[IdentityMapping]:
        rows = await self.session.scalars(
            select(IdentityMapping).where(
                IdentityMapping.organization_id == organization_id,
                IdentityMapping.status != "verified",
            )
        )
        return list(rows)

    async def field_mappings(self, organization_id: UUID) -> list[JiraFieldMapping]:
        rows = await self.session.scalars(
            select(JiraFieldMapping).where(JiraFieldMapping.organization_id == organization_id)
        )
        return list(rows)

    async def integration_configurations(
        self, organization_id: UUID
    ) -> list[IntegrationConfiguration]:
        rows = await self.session.scalars(
            select(IntegrationConfiguration).where(
                IntegrationConfiguration.organization_id == organization_id
            )
        )
        return list(rows)

    async def latest_successful_runs(
        self, organization_id: UUID
    ) -> dict[IntegrationSource, IntegrationRun]:
        result: dict[IntegrationSource, IntegrationRun] = {}
        for source in IntegrationSource:
            run = await self.session.scalar(
                select(IntegrationRun)
                .where(
                    IntegrationRun.organization_id == organization_id,
                    IntegrationRun.source == source,
                    IntegrationRun.status.in_(
                        [IntegrationRunStatus.SUCCEEDED, IntegrationRunStatus.PARTIAL]
                    ),
                )
                .order_by(IntegrationRun.completed_at.desc())
                .limit(1)
            )
            if run:
                result[source] = run
        return result
