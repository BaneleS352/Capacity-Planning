import hashlib
import hmac
import json
import time

from tests.conftest import ApiContext


async def test_end_to_end_planning_flow(api_context: ApiContext) -> None:
    client = api_context.client
    headers = api_context.headers

    response = await client.post(
        "/api/v1/teams",
        headers=headers,
        json={"name": "Payments", "slug": "payments", "location_code": "ZA"},
    )
    assert response.status_code == 201, response.text
    team_id = response.json()["id"]

    response = await client.post(
        "/api/v1/employees",
        headers=headers,
        json={
            "payspace_employee_number": "EMP-1",
            "jira_account_id": "jira-1",
            "corporate_email": "amanda@example.com",
            "full_name": "Amanda Engineer",
            "role_name": "Backend Developer",
            "location_code": "ZA",
            "contract_hours_per_day": "8",
            "fte_factor": "1",
        },
    )
    assert response.status_code == 201, response.text
    employee_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/teams/{team_id}/memberships",
        headers=headers,
        json={
            "employee_id": employee_id,
            "allocation_percent": "100",
            "delivery_role": "Backend Developer",
            "critical_role": True,
            "start_date": "2026-06-01",
        },
    )
    assert response.status_code == 201, response.text

    response = await client.post(
        "/api/v1/sprints",
        headers=headers,
        json={
            "team_id": team_id,
            "jira_sprint_id": "jira-sprint-10",
            "name": "Sprint 10",
            "state": "active",
            "start_at": "2026-06-15T08:00:00Z",
            "end_at": "2026-06-26T17:00:00Z",
        },
    )
    assert response.status_code == 201, response.text
    sprint_id = response.json()["id"]

    response = await client.post(
        "/api/v1/integrations/jira/issues:upsert",
        headers=headers,
        json=[
            {
                "sprint_id": sprint_id,
                "jira_site_id": "site-1",
                "external_id": "10001",
                "issue_key": "PAY-1",
                "summary": "Implement retries",
                "assignee_employee_id": employee_id,
                "status": "Done",
                "status_category": "Done",
                "priority": "High",
                "issue_type": "Story",
                "story_points": "8",
                "blocked": False,
                "source_updated_at": "2026-06-18T08:00:00Z",
            }
        ],
    )
    assert response.status_code == 200, response.text

    response = await client.post(
        "/api/v1/admin/recalculate-capacity",
        headers=headers,
        json={"sprint_id": sprint_id, "synchronous": True},
    )
    assert response.status_code == 202, response.text
    result = response.json()
    assert result["status"] == "completed"
    assert result["summary"]["available_hours"] == "56.00"
    assert result["summary"]["committed_story_points"] == "8.00"
    assert result["summary"]["story_point_capacity"] is None

    response = await client.get(
        f"/api/v1/teams/{team_id}/dashboard",
        params={"sprint_id": sprint_id},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    dashboard = response.json()
    assert dashboard["team"]["name"] == "Payments"
    assert len(dashboard["members"]) == 1
    assert dashboard["members"][0]["capacity"]["assigned_story_points"] == "8.00"
    assert "jira" in dashboard["freshness"]["stale_sources"]

    response = await client.get(
        f"/api/v1/employees/{employee_id}/profile",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    profile = response.json()
    assert profile["employee"]["full_name"] == "Amanda Engineer"
    assert profile["completed_issues"][0]["issue_key"] == "PAY-1"
    assert profile["story_points_history"] == [
        {
            "sprint_id": sprint_id,
            "sprint_name": "Sprint 10",
            "end_at": "2026-06-26T17:00:00",
            "assigned_story_points": "8.00",
            "completed_story_points": "8.00",
            "completed_issue_count": 1,
        }
    ]


async def test_signed_webhook_is_idempotent(api_context: ApiContext) -> None:
    body = {"webhookEvent": "jira:issue_updated", "reason": "must be stripped"}
    raw = json.dumps(body, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"development-jira-secret", timestamp.encode() + b"." + raw, hashlib.sha256
    ).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Organization-ID": str(api_context.organization_id),
        "X-Webhook-ID": "event-1",
        "X-Webhook-Event": "jira:issue_updated",
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Signature": f"sha256={signature}",
    }
    first = await api_context.client.post(
        "/api/v1/integrations/jira/webhook", headers=headers, content=raw
    )
    assert first.status_code == 202, first.text
    assert first.json()["duplicate"] is False
    second = await api_context.client.post(
        "/api/v1/integrations/jira/webhook", headers=headers, content=raw
    )
    assert second.status_code == 202, second.text
    assert second.json()["event_id"] == first.json()["event_id"]
    assert second.json()["duplicate"] is True
