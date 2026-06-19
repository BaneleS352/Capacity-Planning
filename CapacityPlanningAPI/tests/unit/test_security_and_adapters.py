import hashlib
import hmac
import time
from uuid import uuid4

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import validate_webhook_signature
from app.infrastructure.external_services.jira import JiraIssueAdapter
from app.infrastructure.external_services.payspace import PaySpaceAdapter, PaySpaceApiError


def test_webhook_signature_and_replay_window() -> None:
    body = b'{"event":"updated"}'
    timestamp = str(int(time.time()))
    key_material = "test-secret"
    signature = hmac.new(
        key_material.encode(), timestamp.encode() + b"." + body, hashlib.sha256
    ).hexdigest()
    validate_webhook_signature(
        body=body,
        timestamp=timestamp,
        signature=f"sha256={signature}",
        secret=key_material,
        tolerance_seconds=300,
    )
    with pytest.raises(AuthenticationError, match="outside"):
        validate_webhook_signature(
            body=body,
            timestamp=str(int(time.time()) - 1000),
            signature=signature,
            secret=key_material,
            tolerance_seconds=300,
        )


def test_jira_adapter_uses_configured_story_point_field() -> None:
    employee_id = uuid4()
    adapter = JiraIssueAdapter(
        jira_site_id="site-1",
        field_mapping={"story_points": "customfield_123", "flagged": "customfield_456"},
        employee_by_account_id={"jira-user": employee_id},
    )
    issue = adapter.normalize(
        {
            "id": "10001",
            "key": "PAY-1",
            "fields": {
                "summary": "Implement payment retry",
                "assignee": {"accountId": "jira-user"},
                "status": {"name": "In Progress", "statusCategory": {"name": "In Progress"}},
                "priority": {"name": "High"},
                "issuetype": {"name": "Story"},
                "customfield_123": 8,
                "customfield_456": ["Impediment"],
                "updated": "2026-06-18T08:00:00Z",
            },
        },
        uuid4(),
    )
    assert issue.story_points == 8
    assert issue.assignee_employee_id == employee_id
    assert issue.blocked is True


def test_payspace_adapter_masks_reason_and_requires_identity_mapping() -> None:
    employee_id = uuid4()
    adapter = PaySpaceAdapter({"EMP-1": employee_id})
    leave = adapter.leave(
        {
            "id": "leave-1",
            "employeeNumber": "EMP-1",
            "startDate": "2026-06-20",
            "endDate": "2026-06-21",
            "leaveType": "Sick Leave",
            "reason": "Sensitive detail",
        }
    )
    assert leave.employee_id == employee_id
    assert leave.reason is None
    with pytest.raises(PaySpaceApiError, match="identity mapping"):
        PaySpaceAdapter({}).leave(
            {
                "id": "leave-2",
                "employeeNumber": "UNKNOWN",
                "startDate": "2026-06-20",
                "endDate": "2026-06-21",
                "leaveType": "Annual Leave",
            }
        )
