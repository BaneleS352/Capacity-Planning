from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import Page, Pagination, make_page
from app.application.services import AuthorizationService, CatalogService
from app.core.exceptions import AuthorizationError
from app.core.security import Principal, Role, require_permissions
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories import PlanningRepository
from app.models import SprintCommitmentSnapshot
from app.models.entities import SnapshotType, SprintState
from app.schemas.contracts import (
    JiraIssueRead,
    SprintCreate,
    SprintRead,
    SprintSnapshotRead,
    SprintTimelineRead,
    SprintUpdate,
)

router = APIRouter(prefix="/sprints", tags=["sprints"])


@router.get("", response_model=Page[SprintRead])
async def list_sprints(
    pagination: Pagination = Depends(),
    team_id: UUID | None = None,
    state: SprintState | None = None,
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> Page[SprintRead]:
    if Role.SYSTEM_ADMIN not in principal.roles:
        if team_id is None:
            raise AuthorizationError("A team_id is required for scoped sprint listing")
        AuthorizationService(session).require_team(principal, team_id)
    items, total = await PlanningRepository(session).list_sprints(
        principal.organization_id,
        team_id=team_id,
        state=state,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return make_page([SprintRead.model_validate(item) for item in items], total, pagination)


@router.post("", response_model=SprintRead, status_code=status.HTTP_201_CREATED)
async def create_sprint(
    payload: SprintCreate,
    principal: Principal = Depends(require_permissions("planning:write")),
    session: AsyncSession = Depends(get_session),
) -> SprintRead:
    AuthorizationService(session).require_team(principal, payload.team_id)
    return SprintRead.model_validate(
        await CatalogService(session).create_sprint(principal, payload)
    )


@router.get("/{sprint_id}", response_model=SprintRead)
async def get_sprint(
    sprint_id: UUID,
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> SprintRead:
    sprint = await PlanningRepository(session).get_sprint(principal.organization_id, sprint_id)
    AuthorizationService(session).require_team(principal, sprint.team_id)
    return SprintRead.model_validate(sprint)


@router.patch("/{sprint_id}", response_model=SprintRead)
async def update_sprint(
    sprint_id: UUID,
    payload: SprintUpdate,
    principal: Principal = Depends(require_permissions("planning:write")),
    session: AsyncSession = Depends(get_session),
) -> SprintRead:
    sprint = await PlanningRepository(session).get_sprint(principal.organization_id, sprint_id)
    AuthorizationService(session).require_team(principal, sprint.team_id)
    return SprintRead.model_validate(
        await CatalogService(session).update_sprint(principal, sprint_id, payload)
    )


@router.post(
    "/{sprint_id}/snapshots",
    response_model=SprintSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
async def capture_sprint_snapshot(
    sprint_id: UUID,
    snapshot_type: SnapshotType,
    principal: Principal = Depends(require_permissions("planning:write")),
    session: AsyncSession = Depends(get_session),
) -> SprintSnapshotRead:
    sprint = await PlanningRepository(session).get_sprint(principal.organization_id, sprint_id)
    AuthorizationService(session).require_team(principal, sprint.team_id)
    snapshot = await CatalogService(session).capture_sprint_snapshot(
        principal, sprint_id, snapshot_type
    )
    return SprintSnapshotRead.model_validate(snapshot)


@router.get("/{sprint_id}/timeline", response_model=SprintTimelineRead)
async def sprint_timeline(
    sprint_id: UUID,
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> SprintTimelineRead:
    repository = PlanningRepository(session)
    sprint = await repository.get_sprint(principal.organization_id, sprint_id)
    AuthorizationService(session).require_team(principal, sprint.team_id)
    snapshots = list(
        await session.scalars(
            select(SprintCommitmentSnapshot)
            .where(SprintCommitmentSnapshot.sprint_id == sprint_id)
            .order_by(SprintCommitmentSnapshot.captured_at)
        )
    )
    issues = await repository.issues(principal.organization_id, sprint_id=sprint_id, limit=10000)
    return SprintTimelineRead(
        sprint=SprintRead.model_validate(sprint),
        snapshots=[SprintSnapshotRead.model_validate(item) for item in snapshots],
        issues=[JiraIssueRead.model_validate(item) for item in issues],
    )


@router.get("/{sprint_id}/burndown", response_model=list[dict[str, str]])
async def sprint_burndown(
    sprint_id: UUID,
    principal: Principal = Depends(require_permissions("team:read")),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str]]:
    sprint = await PlanningRepository(session).get_sprint(principal.organization_id, sprint_id)
    AuthorizationService(session).require_team(principal, sprint.team_id)
    snapshots = await session.scalars(
        select(SprintCommitmentSnapshot)
        .where(SprintCommitmentSnapshot.sprint_id == sprint_id)
        .order_by(SprintCommitmentSnapshot.captured_at)
    )
    return [
        {
            "captured_at": item.captured_at.isoformat(),
            "remaining_story_points": str(
                max(
                    Decimal("0"),
                    item.committed_story_points
                    + item.added_story_points
                    - item.removed_story_points
                    - item.completed_story_points,
                )
            ),
        }
        for item in snapshots
    ]
