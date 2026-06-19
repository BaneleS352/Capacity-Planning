from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import Page, Pagination, make_page
from app.application.services import AuthorizationService, CatalogService, DashboardService
from app.core.security import Principal, Role, require_permissions
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories import EmployeeRepository, PlanningRepository
from app.schemas.contracts import (
    EmployeeCapacityRead,
    EmployeeCreate,
    EmployeeProfileRead,
    EmployeeRead,
    EmployeeUpdate,
    JiraIssueRead,
    LeaveCreate,
    LeaveRead,
)

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=Page[EmployeeRead])
async def list_employees(
    pagination: Pagination = Depends(),
    search: str | None = Query(default=None, max_length=200),
    role_name: str | None = Query(default=None, max_length=120),
    active: bool | None = None,
    sort: str = Query(default="name", pattern=r"^-?(name|role)$"),
    principal: Principal = Depends(require_permissions("employee:read")),
    session: AsyncSession = Depends(get_session),
) -> Page[EmployeeRead]:
    unrestricted = Role.SYSTEM_ADMIN in principal.roles or Role.HR_ADMIN in principal.roles
    items, total = await EmployeeRepository(session).list_page(
        principal.organization_id,
        offset=pagination.offset,
        limit=pagination.page_size,
        search=search,
        role_name=role_name,
        active=active,
        allowed_team_ids=None if unrestricted else principal.team_ids,
        sort=sort,
    )
    return make_page([EmployeeRead.model_validate(item) for item in items], total, pagination)


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    principal: Principal = Depends(require_permissions("employee:write")),
    session: AsyncSession = Depends(get_session),
) -> EmployeeRead:
    return EmployeeRead.model_validate(
        await CatalogService(session).create_employee(principal, payload)
    )


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: UUID,
    principal: Principal = Depends(require_permissions("employee:read")),
    session: AsyncSession = Depends(get_session),
) -> EmployeeRead:
    await AuthorizationService(session).require_employee(principal, employee_id)
    return EmployeeRead.model_validate(
        await EmployeeRepository(session).get(principal.organization_id, employee_id)
    )


@router.patch("/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: UUID,
    payload: EmployeeUpdate,
    principal: Principal = Depends(require_permissions("employee:write")),
    session: AsyncSession = Depends(get_session),
) -> EmployeeRead:
    return EmployeeRead.model_validate(
        await CatalogService(session).update_employee(principal, employee_id, payload)
    )


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def retire_employee(
    employee_id: UUID,
    principal: Principal = Depends(require_permissions("employee:write")),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await CatalogService(session).update_employee(
        principal, employee_id, EmployeeUpdate(active=False)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{employee_id}/profile", response_model=EmployeeProfileRead)
async def get_employee_profile(
    employee_id: UUID,
    principal: Principal = Depends(require_permissions("employee:read")),
    session: AsyncSession = Depends(get_session),
) -> EmployeeProfileRead:
    await AuthorizationService(session).require_employee(principal, employee_id)
    return await DashboardService(session).employee_profile(
        principal, employee_id, principal.has_permission("leave:reason:read")
    )


@router.get("/{employee_id}/capacity", response_model=list[EmployeeCapacityRead])
async def get_employee_capacity(
    employee_id: UUID,
    sprint_id: UUID | None = None,
    principal: Principal = Depends(require_permissions("employee:read")),
    session: AsyncSession = Depends(get_session),
) -> list[EmployeeCapacityRead]:
    await AuthorizationService(session).require_employee(principal, employee_id)
    repository = PlanningRepository(session)
    items = (
        await repository.employee_snapshots(sprint_id, employee_id)
        if sprint_id
        else await repository.historical_employee_snapshots(employee_id)
    )
    return [EmployeeCapacityRead.model_validate(item) for item in items]


@router.get("/{employee_id}/jira-issues", response_model=list[JiraIssueRead])
async def get_employee_issues(
    employee_id: UUID,
    sprint_id: UUID | None = None,
    principal: Principal = Depends(require_permissions("employee:read")),
    session: AsyncSession = Depends(get_session),
) -> list[JiraIssueRead]:
    await AuthorizationService(session).require_employee(principal, employee_id)
    items = await PlanningRepository(session).issues(
        principal.organization_id, sprint_id=sprint_id, employee_id=employee_id, limit=1000
    )
    return [JiraIssueRead.model_validate(item) for item in items]


@router.post("/{employee_id}/leave", response_model=LeaveRead, status_code=status.HTTP_201_CREATED)
async def create_leave(
    employee_id: UUID,
    payload: LeaveCreate,
    principal: Principal = Depends(require_permissions("employee:write")),
    session: AsyncSession = Depends(get_session),
) -> LeaveRead:
    if payload.employee_id != employee_id:
        from app.core.exceptions import ConflictError

        raise ConflictError(
            "Path employee_id and payload employee_id must match", "identifier_mismatch"
        )
    return LeaveRead.model_validate(await CatalogService(session).create_leave(principal, payload))
