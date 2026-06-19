from collections.abc import AsyncIterator, Mapping
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from app.schemas.contracts import EmployeeCreate, LeaveCreate


class PaySpaceApiError(RuntimeError):
    pass


class PaySpaceEmployeeDTO(BaseModel):
    model_config = ConfigDict(extra="allow")
    employee_number: str = Field(alias="employeeNumber")
    email: str
    full_name: str = Field(alias="fullName")
    position: str
    department: str | None = None
    manager_employee_number: str | None = Field(default=None, alias="managerEmployeeNumber")
    employment_type: str = Field(default="employee", alias="employmentType")
    location_code: str | None = Field(default=None, alias="locationCode")
    contract_hours_per_day: Decimal = Field(default=Decimal("8"), alias="contractHoursPerDay")
    fte_factor: Decimal = Field(default=Decimal("1"), alias="fteFactor")
    active: bool = True


class PaySpaceLeaveDTO(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    employee_number: str = Field(alias="employeeNumber")
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    leave_type: str = Field(alias="leaveType")
    reason: str | None = None
    hours: Decimal | None = None
    status: str = "approved"


class PaySpaceClient:
    """Tenant-neutral client; endpoint paths remain configuration because contracts vary."""

    def __init__(self, base_url: str, access_token: str, timeout_seconds: float = 20.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            timeout=timeout_seconds,
        )

    async def __aenter__(self) -> "PaySpaceClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, PaySpaceApiError)),
        wait=wait_exponential_jitter(initial=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def get(self, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        response = await self._client.get(path, params=params)
        if response.status_code == 429 or response.status_code >= 500:
            raise PaySpaceApiError(f"PaySpace temporarily returned HTTP {response.status_code}")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise PaySpaceApiError("PaySpace returned an unexpected response shape")
        return payload

    async def iter_endpoint(
        self,
        path: str,
        *,
        item_key: str = "items",
        page_size: int = 200,
    ) -> AsyncIterator[dict[str, Any]]:
        page = 1
        while True:
            payload = await self.get(path, {"page": page, "pageSize": page_size})
            items = payload.get(item_key, [])
            if not isinstance(items, list):
                raise PaySpaceApiError(f"PaySpace response field '{item_key}' is not a list")
            for item in items:
                if isinstance(item, dict):
                    yield item
            if not items or payload.get("hasNext") is False or len(items) < page_size:
                break
            page += 1


class PaySpaceAdapter:
    def __init__(self, employee_id_by_number: Mapping[str, UUID]) -> None:
        self.employee_id_by_number = employee_id_by_number

    def employee(self, raw: dict[str, Any]) -> EmployeeCreate:
        value = PaySpaceEmployeeDTO.model_validate(raw)
        return EmployeeCreate(
            payspace_employee_number=value.employee_number,
            corporate_email=value.email,
            full_name=value.full_name,
            role_name=value.position,
            department=value.department,
            employment_type=value.employment_type,
            location_code=value.location_code,
            contract_hours_per_day=value.contract_hours_per_day,
            fte_factor=value.fte_factor,
        )

    def leave(self, raw: dict[str, Any], *, include_reason: bool = False) -> LeaveCreate:
        value = PaySpaceLeaveDTO.model_validate(raw)
        try:
            employee_id = self.employee_id_by_number[value.employee_number]
        except KeyError as exc:
            raise PaySpaceApiError(
                f"Employee {value.employee_number} has no verified identity mapping"
            ) from exc
        return LeaveCreate(
            employee_id=employee_id,
            start_date=value.start_date,
            end_date=value.end_date,
            leave_type=value.leave_type,
            reason=value.reason if include_reason else None,
            partial_day_hours=value.hours,
            status=value.status,
            source_reference_id=value.id,
        )
