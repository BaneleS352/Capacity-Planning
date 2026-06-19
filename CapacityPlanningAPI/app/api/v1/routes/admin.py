from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import AdminService, CapacityPlanningService, CatalogService
from app.core.security import Principal, require_permissions
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories import AdminRepository
from app.models import CapacityProfile, IntegrationRun, PublicHoliday, RiskThreshold
from app.schemas.contracts import (
    CapacityProfileRead,
    CapacityProfileUpsert,
    IdentityMappingRead,
    IdentityMappingResolve,
    IntegrationConfigurationRead,
    IntegrationConfigurationUpsert,
    IntegrationRunRead,
    JiraFieldMappingRead,
    JiraFieldMappingUpsert,
    PublicHolidayCreate,
    PublicHolidayRead,
    RecalculationRequest,
    RecalculationResponse,
    RiskThresholdRead,
    RiskThresholdUpsert,
    TeamCapacityRead,
)
from app.workers.tasks import enqueue_capacity_recalculation

router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/jira/field-mappings", response_model=list[JiraFieldMappingRead])
async def list_field_mappings(
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[JiraFieldMappingRead]:
    items = await AdminRepository(session).field_mappings(principal.organization_id)
    return [JiraFieldMappingRead.model_validate(item) for item in items]


@router.put("/jira/field-mappings", response_model=JiraFieldMappingRead)
async def upsert_field_mapping(
    payload: JiraFieldMappingUpsert,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> JiraFieldMappingRead:
    return JiraFieldMappingRead.model_validate(
        await AdminService(session).upsert_field_mapping(principal, payload)
    )


@router.get("/identity-mappings/unresolved", response_model=list[IdentityMappingRead])
async def unresolved_identity_mappings(
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[IdentityMappingRead]:
    items = await AdminRepository(session).unresolved_mappings(principal.organization_id)
    return [IdentityMappingRead.model_validate(item) for item in items]


@router.patch("/identity-mappings/{mapping_id}", response_model=IdentityMappingRead)
async def resolve_identity_mapping(
    mapping_id: UUID,
    payload: IdentityMappingResolve,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> IdentityMappingRead:
    return IdentityMappingRead.model_validate(
        await AdminService(session).resolve_identity(
            principal, mapping_id, payload.employee_id, payload.match_method
        )
    )


@router.get("/capacity-profiles", response_model=list[CapacityProfileRead])
async def list_capacity_profiles(
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[CapacityProfileRead]:
    items = await session.scalars(
        select(CapacityProfile)
        .where(CapacityProfile.organization_id == principal.organization_id)
        .order_by(CapacityProfile.role_name)
    )
    return [CapacityProfileRead.model_validate(item) for item in items]


@router.put("/capacity-profiles/{role_name}", response_model=CapacityProfileRead)
async def upsert_capacity_profile(
    role_name: str,
    payload: CapacityProfileUpsert,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> CapacityProfileRead:
    if payload.role_name != role_name:
        from app.core.exceptions import ConflictError

        raise ConflictError(
            "Path role_name and payload role_name must match", "identifier_mismatch"
        )
    return CapacityProfileRead.model_validate(
        await CatalogService(session).upsert_profile(principal, payload)
    )


@router.get("/public-holidays", response_model=list[PublicHolidayRead])
async def list_public_holidays(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    location_code: str | None = Query(default=None, max_length=32),
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[PublicHolidayRead]:
    filters = [PublicHoliday.organization_id == principal.organization_id]
    if from_date:
        filters.append(PublicHoliday.holiday_date >= from_date)
    if to_date:
        filters.append(PublicHoliday.holiday_date <= to_date)
    if location_code:
        filters.append(PublicHoliday.location_code == location_code)
    items = await session.scalars(
        select(PublicHoliday).where(*filters).order_by(PublicHoliday.holiday_date)
    )
    return [PublicHolidayRead.model_validate(item) for item in items]


@router.post(
    "/public-holidays", response_model=PublicHolidayRead, status_code=status.HTTP_201_CREATED
)
async def create_public_holiday(
    payload: PublicHolidayCreate,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> PublicHolidayRead:
    return PublicHolidayRead.model_validate(
        await CatalogService(session).create_holiday(principal, payload)
    )


@router.get("/risk-thresholds", response_model=list[RiskThresholdRead])
async def list_risk_thresholds(
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[RiskThresholdRead]:
    items = await session.scalars(
        select(RiskThreshold)
        .where(RiskThreshold.organization_id == principal.organization_id)
        .order_by(RiskThreshold.risk_type)
    )
    return [RiskThresholdRead.model_validate(item) for item in items]


@router.put("/risk-thresholds/{risk_type}", response_model=RiskThresholdRead)
async def upsert_risk_threshold(
    risk_type: str,
    payload: RiskThresholdUpsert,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> RiskThresholdRead:
    if payload.risk_type != risk_type:
        from app.core.exceptions import ConflictError

        raise ConflictError(
            "Path risk_type and payload risk_type must match", "identifier_mismatch"
        )
    return RiskThresholdRead.model_validate(
        await AdminService(session).upsert_threshold(principal, payload)
    )


@router.get("/integrations", response_model=list[IntegrationConfigurationRead])
async def list_integrations(
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[IntegrationConfigurationRead]:
    items = await AdminRepository(session).integration_configurations(principal.organization_id)
    return [IntegrationConfigurationRead.model_validate(item) for item in items]


@router.put("/integrations/{name}", response_model=IntegrationConfigurationRead)
async def upsert_integration(
    name: str,
    payload: IntegrationConfigurationUpsert,
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> IntegrationConfigurationRead:
    if payload.name != name:
        from app.core.exceptions import ConflictError

        raise ConflictError("Path name and payload name must match", "identifier_mismatch")
    return IntegrationConfigurationRead.model_validate(
        await AdminService(session).upsert_integration_configuration(principal, payload)
    )


@router.get("/integration-runs", response_model=list[IntegrationRunRead])
async def list_integration_runs(
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[IntegrationRunRead]:
    items = await session.scalars(
        select(IntegrationRun)
        .where(IntegrationRun.organization_id == principal.organization_id)
        .order_by(IntegrationRun.started_at.desc())
        .limit(limit)
    )
    return [IntegrationRunRead.model_validate(item) for item in items]


@router.post(
    "/recalculate-capacity",
    response_model=RecalculationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def recalculate_capacity(
    payload: RecalculationRequest,
    principal: Principal = Depends(require_permissions("planning:write")),
    session: AsyncSession = Depends(get_session),
) -> RecalculationResponse:
    from app.infrastructure.repositories import PlanningRepository

    sprint = await PlanningRepository(session).get_sprint(
        principal.organization_id, payload.sprint_id
    )
    if not principal.can_access_team(sprint.team_id):
        from app.core.exceptions import AuthorizationError

        raise AuthorizationError("You are not authorized for this sprint")
    if payload.synchronous:
        summary = await CapacityPlanningService(session).recalculate(
            principal.organization_id, payload.sprint_id
        )
        return RecalculationResponse(
            sprint_id=payload.sprint_id,
            status="completed",
            summary=TeamCapacityRead.model_validate(summary),
        )
    enqueue_capacity_recalculation(principal.organization_id, payload.sprint_id)
    return RecalculationResponse(sprint_id=payload.sprint_id, status="accepted")
