from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.core.config import Settings, get_settings
from app.core.security import Principal, get_current_principal
from app.infrastructure.database.session import get_session
from app.schemas.contracts import CurrentUserRead, HealthRead

router = APIRouter(tags=["system"])


@router.get("/health/live", response_model=HealthRead, include_in_schema=False)
async def liveness(settings: Settings = Depends(get_settings)) -> HealthRead:
    return HealthRead(status="ok", version=__version__, environment=settings.environment)


@router.get("/health/ready", response_model=HealthRead, include_in_schema=False)
async def readiness(
    session: AsyncSession = Depends(get_session), settings: Settings = Depends(get_settings)
) -> HealthRead:
    await session.execute(text("SELECT 1"))
    return HealthRead(
        status="ok", version=__version__, environment=settings.environment, database="ok"
    )


@router.get("/auth/me", response_model=CurrentUserRead, summary="Return authenticated context")
async def current_user(principal: Principal = Depends(get_current_principal)) -> CurrentUserRead:
    return CurrentUserRead(
        subject=principal.subject,
        organization_id=principal.organization_id,
        user_id=principal.user_id,
        email=principal.email,
        roles=sorted(principal.roles, key=str),
        team_ids=sorted(principal.team_ids, key=str),
        permissions=sorted(principal.permissions),
    )
