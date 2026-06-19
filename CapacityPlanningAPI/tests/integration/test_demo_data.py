from sqlalchemy import func, select

from app.demo_data import _ensure_data_science_workspace
from app.models import Employee, JiraIssue, Organization, Sprint, Team, TeamMembership
from tests.conftest import ApiContext


async def test_data_science_demo_seed_is_complete_and_idempotent(
    api_context: ApiContext,
) -> None:
    organization = await api_context.session.get(Organization, api_context.organization_id)
    assert organization is not None

    first_sprint_id = await _ensure_data_science_workspace(api_context.session, organization)
    await api_context.session.commit()
    second_sprint_id = await _ensure_data_science_workspace(api_context.session, organization)
    await api_context.session.commit()

    assert second_sprint_id == first_sprint_id
    team = await api_context.session.scalar(
        select(Team).where(Team.organization_id == organization.id, Team.slug == "data-science")
    )
    assert team is not None
    assert team.department == "Data & Analytics"
    assert team.settings["portfolio"] == "Technology"

    employee_count = await api_context.session.scalar(
        select(func.count()).select_from(Employee).where(
            Employee.organization_id == organization.id,
            Employee.department == "Data & Analytics",
        )
    )
    membership_count = await api_context.session.scalar(
        select(func.count()).select_from(TeamMembership).where(TeamMembership.team_id == team.id)
    )
    sprint_count = await api_context.session.scalar(
        select(func.count()).select_from(Sprint).where(Sprint.team_id == team.id)
    )
    issue_count = await api_context.session.scalar(
        select(func.count()).select_from(JiraIssue).where(
            JiraIssue.organization_id == organization.id,
            JiraIssue.issue_key.like("DS-%"),
        )
    )

    assert employee_count == 5
    assert membership_count == 5
    assert sprint_count == 6
    assert issue_count == 7
