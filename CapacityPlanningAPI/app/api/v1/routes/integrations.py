from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import CatalogService, IntegrationService
from app.core.config import Settings, get_settings
from app.core.security import Principal, require_permissions, validate_webhook_signature
from app.infrastructure.database.session import get_session
from app.models.entities import IntegrationSource
from app.schemas.contracts import (
    EmployeeCreate,
    EmployeeRead,
    JiraIssueRead,
    JiraIssueUpsert,
    LeaveCreate,
    LeaveRead,
    WebhookAccepted,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


async def _accept_webhook(
    source: IntegrationSource,
    request: Request,
    organization_id: UUID,
    event_id: str,
    event_type: str,
    timestamp: str,
    signature: str,
    settings: Settings,
    session: AsyncSession,
) -> WebhookAccepted:
    body = await request.body()
    secret = (
        settings.jira_webhook_secret.get_secret_value()
        if source == IntegrationSource.JIRA
        else settings.payspace_webhook_secret.get_secret_value()
    )
    validate_webhook_signature(
        body=body,
        timestamp=timestamp,
        signature=signature,
        secret=secret,
        tolerance_seconds=settings.webhook_tolerance_seconds,
    )
    event, duplicate = await IntegrationService(session).accept_webhook(
        organization_id, source, event_id, event_type, body
    )
    return WebhookAccepted(event_id=event.id, duplicate=duplicate)


@router.post("/jira/webhook", response_model=WebhookAccepted, status_code=status.HTTP_202_ACCEPTED)
async def jira_webhook(
    request: Request,
    organization_id: UUID = Header(alias="X-Organization-ID"),
    event_id: str = Header(alias="X-Webhook-ID", max_length=255),
    event_type: str = Header(alias="X-Webhook-Event", max_length=150),
    timestamp: str = Header(alias="X-Webhook-Timestamp"),
    signature: str = Header(alias="X-Webhook-Signature"),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> WebhookAccepted:
    return await _accept_webhook(
        IntegrationSource.JIRA,
        request,
        organization_id,
        event_id,
        event_type,
        timestamp,
        signature,
        settings,
        session,
    )


@router.post(
    "/payspace/webhook", response_model=WebhookAccepted, status_code=status.HTTP_202_ACCEPTED
)
async def payspace_webhook(
    request: Request,
    organization_id: UUID = Header(alias="X-Organization-ID"),
    event_id: str = Header(alias="X-Webhook-ID", max_length=255),
    event_type: str = Header(alias="X-Webhook-Event", max_length=150),
    timestamp: str = Header(alias="X-Webhook-Timestamp"),
    signature: str = Header(alias="X-Webhook-Signature"),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> WebhookAccepted:
    return await _accept_webhook(
        IntegrationSource.PAYSPACE,
        request,
        organization_id,
        event_id,
        event_type,
        timestamp,
        signature,
        settings,
        session,
    )


@router.post("/jira/issues:upsert", response_model=list[JiraIssueRead])
async def upsert_jira_issues(
    payload: list[JiraIssueUpsert],
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[JiraIssueRead]:
    service = CatalogService(session)
    return [
        JiraIssueRead.model_validate(await service.upsert_jira_issue(principal, item))
        for item in payload
    ]


@router.post("/payspace/employees:upsert", response_model=list[EmployeeRead])
async def upsert_payspace_employees(
    payload: list[EmployeeCreate],
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[EmployeeRead]:
    service = CatalogService(session)
    return [
        EmployeeRead.model_validate(await service.upsert_payspace_employee(principal, item))
        for item in payload
    ]


@router.post("/payspace/leave:upsert", response_model=list[LeaveRead])
async def upsert_payspace_leave(
    payload: list[LeaveCreate],
    principal: Principal = Depends(require_permissions("*")),
    session: AsyncSession = Depends(get_session),
) -> list[LeaveRead]:
    service = CatalogService(session)
    return [
        LeaveRead.model_validate(await service.upsert_payspace_leave(principal, item))
        for item in payload
    ]
