from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import AuthorizationService
from app.core.security import Principal, require_permissions
from app.infrastructure.database.session import get_session
from app.models import Sprint, TeamCapacitySummary
from app.schemas.contracts import PlannedVsActualRead

router = APIRouter(prefix="/reports", tags=["reporting"])


@router.get("/planned-vs-actual", response_model=list[PlannedVsActualRead])
async def planned_vs_actual(
    team_id: UUID,
    limit: int = Query(default=12, ge=1, le=100),
    principal: Principal = Depends(require_permissions("report:read")),
    session: AsyncSession = Depends(get_session),
) -> list[PlannedVsActualRead]:
    AuthorizationService(session).require_team(principal, team_id)
    rows = await session.execute(
        select(Sprint, TeamCapacitySummary)
        .join(TeamCapacitySummary, TeamCapacitySummary.sprint_id == Sprint.id)
        .where(Sprint.team_id == team_id)
        .order_by(Sprint.end_at.desc())
        .limit(limit)
    )
    result: list[PlannedVsActualRead] = []
    for sprint, summary in rows:
        delivery = (
            (
                summary.completed_story_points / summary.committed_story_points * Decimal("100")
            ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            if summary.committed_story_points > 0
            else None
        )
        result.append(
            PlannedVsActualRead(
                sprint_id=sprint.id,
                sprint_name=sprint.name,
                committed_story_points=summary.committed_story_points,
                added_story_points=summary.added_story_points,
                removed_story_points=summary.removed_story_points,
                completed_story_points=summary.completed_story_points,
                carry_over_story_points=summary.remaining_story_points,
                delivery_percent=delivery,
            )
        )
    return result
