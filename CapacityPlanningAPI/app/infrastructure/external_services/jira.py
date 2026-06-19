from collections.abc import AsyncIterator, Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from app.schemas.contracts import JiraIssueUpsert


class JiraApiError(RuntimeError):
    pass


class JiraUserDTO(BaseModel):
    model_config = ConfigDict(extra="allow")
    accountId: str | None = None
    emailAddress: str | None = None


class JiraStatusCategoryDTO(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = "Unknown"


class JiraStatusDTO(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    statusCategory: JiraStatusCategoryDTO = Field(default_factory=JiraStatusCategoryDTO)


class JiraNamedDTO(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str


class JiraIssueDTO(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    key: str
    fields: dict[str, Any]


class JiraClient:
    def __init__(
        self,
        base_url: str,
        *,
        bearer_token: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        headers = {"Accept": "application/json"}
        auth: httpx.Auth | None = None
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        elif email and api_token:
            auth = httpx.BasicAuth(email, api_token)
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"), headers=headers, auth=auth, timeout=timeout_seconds
        )

    async def __aenter__(self) -> "JiraClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, JiraApiError)),
        wait=wait_exponential_jitter(initial=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def get(self, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        response = await self._client.get(path, params=params)
        if response.status_code == 429 or response.status_code >= 500:
            raise JiraApiError(f"Jira temporarily returned HTTP {response.status_code}")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise JiraApiError("Jira returned an unexpected response shape")
        return payload

    async def iter_pages(
        self,
        path: str,
        *,
        item_key: str,
        params: Mapping[str, Any] | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[dict[str, Any]]:
        start_at = 0
        while True:
            page_params = dict(params or {})
            page_params.update(startAt=start_at, maxResults=page_size)
            payload = await self.get(path, page_params)
            items = payload.get(item_key, [])
            if not isinstance(items, list):
                raise JiraApiError(f"Jira response field '{item_key}' is not a list")
            for item in items:
                if isinstance(item, dict):
                    yield item
            start_at += len(items)
            total = int(payload.get("total", start_at))
            if not items or start_at >= total or payload.get("isLast") is True:
                break

    def boards(self) -> AsyncIterator[dict[str, Any]]:
        return self.iter_pages("/rest/agile/1.0/board", item_key="values")

    def sprints(self, board_id: str) -> AsyncIterator[dict[str, Any]]:
        return self.iter_pages(f"/rest/agile/1.0/board/{board_id}/sprint", item_key="values")

    def sprint_issues(self, sprint_id: str) -> AsyncIterator[dict[str, Any]]:
        return self.iter_pages(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            item_key="issues",
            params={"expand": "changelog"},
        )


class JiraIssueAdapter:
    def __init__(
        self,
        *,
        jira_site_id: str,
        field_mapping: Mapping[str, str],
        employee_by_account_id: Mapping[str, UUID],
    ) -> None:
        self.jira_site_id = jira_site_id
        self.field_mapping = field_mapping
        self.employee_by_account_id = employee_by_account_id

    def normalize(self, raw: dict[str, Any], sprint_id: UUID | None) -> JiraIssueUpsert:
        issue = JiraIssueDTO.model_validate(raw)
        fields = issue.fields
        status_raw = fields.get("status") or {"name": "Unknown"}
        status = JiraStatusDTO.model_validate(status_raw)
        assignee_raw = fields.get("assignee")
        assignee = JiraUserDTO.model_validate(assignee_raw) if assignee_raw else None
        priority = self._name(fields.get("priority"))
        issue_type = self._name(fields.get("issuetype"))
        story_points = self._decimal(fields.get(self.field_mapping.get("story_points", "")))
        flagged_field = self.field_mapping.get("flagged")
        flagged_value = fields.get(flagged_field) if flagged_field else None
        blocked_field = self.field_mapping.get("blocked")
        blocked_value = fields.get(blocked_field) if blocked_field else None
        updated = fields.get("updated")
        source_updated_at = (
            datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
            if updated
            else datetime.now(UTC)
        )
        return JiraIssueUpsert(
            sprint_id=sprint_id,
            jira_site_id=self.jira_site_id,
            external_id=issue.id,
            issue_key=issue.key,
            summary=str(fields.get("summary") or issue.key),
            assignee_employee_id=(
                self.employee_by_account_id.get(assignee.accountId)
                if assignee and assignee.accountId
                else None
            ),
            status=status.name,
            status_category=status.statusCategory.name,
            priority=priority,
            issue_type=issue_type,
            epic_key=self._epic_key(fields),
            story_points=story_points,
            blocked=bool(blocked_value) or bool(flagged_value),
            flagged=bool(flagged_value),
            completed_at=(
                source_updated_at if status.statusCategory.name.casefold() == "done" else None
            ),
            source_updated_at=source_updated_at,
            normalized_fields={
                "labels": fields.get("labels", []),
                "components": fields.get("components", []),
            },
        )

    @staticmethod
    def _name(value: Any) -> str | None:
        return str(value.get("name")) if isinstance(value, dict) and value.get("name") else None

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        try:
            return Decimal(str(value or 0))
        except InvalidOperation:
            return Decimal("0")

    def _epic_key(self, fields: dict[str, Any]) -> str | None:
        field = self.field_mapping.get("epic")
        value = fields.get(field) if field else None
        if isinstance(value, dict):
            return value.get("key")
        return str(value) if value else None
