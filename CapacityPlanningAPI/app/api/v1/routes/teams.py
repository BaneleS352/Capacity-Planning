from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import Page, Pagination, make_page
from app.application.services import (
    AuthorizationService,
    CatalogService,
    DashboardService,
    RiskManagementService,
)
from app.core.security import Principal, Role, require_permissions
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories import PlanningRepository, TeamRepository
from app.schemas.contracts import (
    MembershipCreate,
    MembershipRead,
    RiskRead,
    TeamCapacityRead,
    TeamCreate,
    TeamDashboardRead,
    TeamRead,
    TeamUpdate,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=Page[TeamRead])
async def list_teams(
    pagination: Pagination = Depends(),
    search: str | None = Query(default=None, max_length=200),
    department: str | None = Query(default=None, max_length=200),
    active: bool | None = None,
    sort: str = Query(default="name", pattern=r"^-?(name|created_at)$"),
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> Page[TeamRead]:
    allowed = None if Role.SYSTEM_ADMIN in principal.roles else principal.team_ids
    items, total = await TeamRepository(session).list_page(
        principal.organization_id,
        offset=pagination.offset,
        limit=pagination.page_size,
        search=search,
        department=department,
        active=active,
        allowed_team_ids=allowed,
        sort=sort,
    )
    return make_page([TeamRead.model_validate(item) for item in items], total, pagination)


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def create_team(
    payload: TeamCreate,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> TeamRead:
    return TeamRead.model_validate(await CatalogService(session).create_team(principal, payload))


@router.get("/{team_id}", response_model=TeamRead)
async def get_team(
    team_id: UUID,
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> TeamRead:
    AuthorizationService(session).require_team(principal, team_id)
    return TeamRead.model_validate(
        await TeamRepository(session).get(principal.organization_id, team_id)
    )


@router.patch("/{team_id}", response_model=TeamRead)
async def update_team(
    team_id: UUID,
    payload: TeamUpdate,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> TeamRead:
    return TeamRead.model_validate(
        await CatalogService(session).update_team(principal, team_id, payload)
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def retire_team(
    team_id: UUID,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await CatalogService(session).update_team(principal, team_id, TeamUpdate(active=False))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{team_id}/memberships", response_model=MembershipRead, status_code=status.HTTP_201_CREATED
)
async def add_membership(
    team_id: UUID,
    payload: MembershipCreate,
    principal: Principal = Depends(require_permissions("planning:write")),
    session: AsyncSession = Depends(get_session),
) -> MembershipRead:
    AuthorizationService(session).require_team(principal, team_id)
    return MembershipRead.model_validate(
        await CatalogService(session).add_membership(principal, team_id, payload)
    )


@router.get("/{team_id}/dashboard", response_model=TeamDashboardRead)
async def get_dashboard(
    team_id: UUID,
    sprint_id: UUID = Query(),
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> TeamDashboardRead:
    AuthorizationService(session).require_team(principal, team_id)
    return await DashboardService(session).team_dashboard(principal, team_id, sprint_id)


@router.get("/{team_id}/capacity", response_model=TeamCapacityRead)
async def get_capacity(
    team_id: UUID,
    sprint_id: UUID = Query(),
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> TeamCapacityRead:
    AuthorizationService(session).require_team(principal, team_id)
    sprint = await PlanningRepository(session).get_sprint(principal.organization_id, sprint_id)
    if sprint.team_id != team_id:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Sprint", sprint_id)
    summary = await PlanningRepository(session).summary(sprint_id)
    if summary is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Capacity summary", sprint_id)
    return TeamCapacityRead.model_validate(summary)


@router.get("/{team_id}/risks", response_model=list[RiskRead])
async def get_risks(
    team_id: UUID,
    sprint_id: UUID | None = None,
    active_only: bool = True,
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> list[RiskRead]:
    AuthorizationService(session).require_team(principal, team_id)
    items = await PlanningRepository(session).risks(
        principal.organization_id, team_id=team_id, sprint_id=sprint_id, active_only=active_only
    )
    return [RiskRead.model_validate(item) for item in items]


@router.patch("/{team_id}/risks/{risk_id}/acknowledge", response_model=RiskRead)
async def acknowledge_risk(
    team_id: UUID,
    risk_id: UUID,
    principal: Principal = Depends(require_permissions("risk:write")),
    session: AsyncSession = Depends(get_session),
) -> RiskRead:
    AuthorizationService(session).require_team(principal, team_id)
    return RiskRead.model_validate(
        await RiskManagementService(session).acknowledge(principal, team_id, risk_id)
    )
