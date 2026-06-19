from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import CapacityPlanningService
from app.infrastructure.database.session import AsyncSessionFactory
from app.models import (
    Employee,
    EmployeeCapacitySnapshot,
    IdentityMapping,
    IntegrationConfiguration,
    IntegrationRun,
    JiraFieldMapping,
    JiraIssue,
    LeaveRecord,
    Organization,
    PublicHoliday,
    Sprint,
    SprintCommitmentSnapshot,
    Team,
    TeamAccess,
    TeamCapacitySummary,
    TeamMembership,
    TeamVelocityMetric,
    User,
)
from app.models.entities import (
    IntegrationRunStatus,
    IntegrationSource,
    SnapshotType,
    SprintState,
)

DEMO_SEED_VERSION = 1
ZERO = Decimal("0")


def _at(day: date, hour: int = 8) -> datetime:
    return datetime.combine(day, time(hour=hour), tzinfo=UTC)


async def seed_demo(organization_id: UUID) -> None:
    active_sprint_ids: list[UUID] = []
    async with AsyncSessionFactory() as session:
        organization = await session.get(Organization, organization_id)
        if organization is None:
            raise RuntimeError(f"Organization {organization_id} does not exist")

        if organization.settings.get("demo_seed_version") == DEMO_SEED_VERSION:
            active_sprint_ids = list(
                await session.scalars(
                    select(Sprint.id)
                    .join(Team, Team.id == Sprint.team_id)
                    .where(
                        Team.organization_id == organization_id,
                        Sprint.state == SprintState.ACTIVE,
                    )
                )
            )
        else:
            active_sprint_ids = await _insert_demo_workspace(session, organization)
            organization.settings = {
                **organization.settings,
                "demo_seed_version": DEMO_SEED_VERSION,
            }

        data_science_sprint_id = await _ensure_data_science_workspace(session, organization)
        if data_science_sprint_id not in active_sprint_ids:
            active_sprint_ids.append(data_science_sprint_id)
        await session.commit()

    async with AsyncSessionFactory() as session:
        service = CapacityPlanningService(session)
        for sprint_id in active_sprint_ids:
            await service.recalculate(organization_id, sprint_id)

    print(
        "Demo data ready: 3 teams, 14 employees, 15 historical sprints, "
        f"{len(active_sprint_ids)} active sprints, leave, Jira work, velocity, and risks."
    )


async def _insert_demo_workspace(session, organization: Organization) -> list[UUID]:  # type: ignore[no-untyped-def]
    today = date.today()
    current_start = today - timedelta(days=today.weekday())
    current_end = current_start + timedelta(days=11)
    now = datetime.now(UTC)

    payments = Team(
        organization_id=organization.id,
        name="Payments Platform",
        slug="payments-platform",
        description="Core payment processing, settlement, and reliability services.",
        department="Digital Engineering",
        timezone="Africa/Johannesburg",
        location_code="ZA",
        velocity_lookback=5,
    )
    channels = Team(
        organization_id=organization.id,
        name="Customer Channels",
        slug="customer-channels",
        description="Web and mobile customer experiences.",
        department="Digital Engineering",
        timezone="Africa/Johannesburg",
        location_code="ZA",
        velocity_lookback=5,
    )
    session.add_all([payments, channels])
    await session.flush()

    employee_specs = [
        (
            "EMP-1001",
            "jira-amanda",
            "amanda.mokoena@example.com",
            "Amanda Mokoena",
            "Backend Developer",
        ),
        (
            "EMP-1002",
            "jira-thabo",
            "thabo.jacobs@example.com",
            "Thabo Jacobs",
            "Frontend Developer",
        ),
        ("EMP-1003", "jira-sizwe", "sizwe.naidoo@example.com", "Sizwe Naidoo", "QA Engineer"),
        ("EMP-1004", "jira-lerato", "lerato.dlamini@example.com", "Lerato Dlamini", "Tech Lead"),
        ("EMP-1005", "jira-priya", "priya.patel@example.com", "Priya Patel", "DevOps Engineer"),
        (
            "EMP-2001",
            "jira-nandi",
            "nandi.khumalo@example.com",
            "Nandi Khumalo",
            "Backend Developer",
        ),
        (
            "EMP-2002",
            "jira-sipho",
            "sipho.mthembu@example.com",
            "Sipho Mthembu",
            "Frontend Developer",
        ),
        ("EMP-2003", "jira-karabo", "karabo.molefe@example.com", "Karabo Molefe", "QA Engineer"),
        ("EMP-2004", "jira-ayanda", "ayanda.zulu@example.com", "Ayanda Zulu", "Business Analyst"),
    ]
    employees: list[Employee] = []
    for number, account_id, email, full_name, role_name in employee_specs:
        employees.append(
            Employee(
                organization_id=organization.id,
                payspace_employee_number=number,
                jira_account_id=account_id,
                corporate_email=email,
                full_name=full_name,
                role_name=role_name,
                department="Digital Engineering",
                location_code="ZA",
                contract_hours_per_day=Decimal("8"),
                fte_factor=Decimal("1"),
                source_updated_at=now - timedelta(minutes=20),
            )
        )
    session.add_all(employees)
    await session.flush()
    by_number = {employee.payspace_employee_number: employee for employee in employees}
    for employee in employees:
        employee_number = employee.payspace_employee_number or ""
        employee.manager_employee_id = (
            by_number["EMP-1004"].id
            if employee_number.startswith("EMP-1") and employee_number != "EMP-1004"
            else None
        )

    system_admin = User(
        organization_id=organization.id,
        external_subject="local-system-admin",
        email="platform.admin@example.com",
        display_name="Platform Administrator",
        roles=["system_admin"],
    )
    manager = User(
        organization_id=organization.id,
        external_subject="demo-development-manager",
        email="lerato.dlamini@example.com",
        display_name="Lerato Dlamini",
        roles=["development_manager"],
    )
    session.add_all([system_admin, manager])
    await session.flush()
    session.add(TeamAccess(user_id=manager.id, team_id=payments.id, access_type="manager"))

    membership_start = current_start - timedelta(days=140)
    payment_allocations = [
        ("EMP-1001", Decimal("100"), False),
        ("EMP-1002", Decimal("100"), False),
        ("EMP-1003", Decimal("100"), True),
        ("EMP-1004", Decimal("100"), True),
        ("EMP-1005", Decimal("50"), True),
    ]
    channel_allocations = [
        ("EMP-2001", Decimal("100"), True),
        ("EMP-2002", Decimal("100"), False),
        ("EMP-2003", Decimal("100"), True),
        ("EMP-2004", Decimal("100"), False),
        ("EMP-1005", Decimal("50"), True),
    ]
    for team, allocations in (
        (payments, payment_allocations),
        (channels, channel_allocations),
    ):
        for employee_number, allocation, critical in allocations:
            employee = by_number[employee_number]
            session.add(
                TeamMembership(
                    team_id=team.id,
                    employee_id=employee.id,
                    allocation_percent=allocation,
                    delivery_role=employee.role_name,
                    critical_role=critical,
                    start_date=membership_start,
                )
            )

    for employee in employees:
        session.add(
            IdentityMapping(
                organization_id=organization.id,
                employee_id=employee.id,
                jira_account_id=employee.jira_account_id,
                payspace_employee_number=employee.payspace_employee_number,
                corporate_email=employee.corporate_email,
                status="verified",
                match_method="corporate_email",
                verified_by_user_id=system_admin.id,
            )
        )

    session.add(
        PublicHoliday(
            organization_id=organization.id,
            location_code="ZA",
            holiday_date=current_start + timedelta(days=1),
            name="Demo Public Holiday",
        )
    )
    session.add_all(
        [
            LeaveRecord(
                employee_id=by_number["EMP-1003"].id,
                start_date=current_start + timedelta(days=7),
                end_date=current_start + timedelta(days=9),
                leave_type="Annual Leave",
                status="approved",
                source_reference_id="DEMO-LEAVE-1003",
                source_updated_at=now - timedelta(minutes=30),
            ),
            LeaveRecord(
                employee_id=by_number["EMP-1005"].id,
                start_date=current_start + timedelta(days=8),
                end_date=current_start + timedelta(days=8),
                leave_type="Family Responsibility Leave",
                partial_day_hours=Decimal("4"),
                status="approved",
                source_reference_id="DEMO-LEAVE-1005",
                source_updated_at=now - timedelta(minutes=30),
            ),
        ]
    )

    payment_history = await _historical_sprints(
        session,
        payments,
        current_start,
        [Decimal("38"), Decimal("42"), Decimal("45"), Decimal("40"), Decimal("44")],
        payment_allocations,
        by_number,
    )
    await _historical_sprints(
        session,
        channels,
        current_start,
        [Decimal("31"), Decimal("35"), Decimal("33"), Decimal("39"), Decimal("37")],
        channel_allocations,
        by_number,
    )

    payment_sprint = Sprint(
        team_id=payments.id,
        jira_sprint_id="PAY-SPRINT-CURRENT",
        name="Payments Current Sprint",
        state=SprintState.ACTIVE,
        start_at=_at(current_start),
        end_at=_at(current_end, 17),
        goal="Improve payment resilience and settlement observability.",
        source_updated_at=now - timedelta(minutes=10),
    )
    channel_sprint = Sprint(
        team_id=channels.id,
        jira_sprint_id="CHN-SPRINT-CURRENT",
        name="Channels Current Sprint",
        state=SprintState.ACTIVE,
        start_at=_at(current_start),
        end_at=_at(current_end, 17),
        goal="Release the simplified onboarding journey.",
        source_updated_at=now - timedelta(minutes=10),
    )
    session.add_all([payment_sprint, channel_sprint])
    await session.flush()

    payment_issues = [
        _issue(
            organization.id,
            payment_sprint,
            "PAY-101",
            "Add settlement metrics",
            by_number["EMP-1001"],
            "Done",
            "Done",
            "8",
            now,
        ),
        _issue(
            organization.id,
            payment_sprint,
            "PAY-102",
            "Implement payment retries",
            by_number["EMP-1001"],
            "In Progress",
            "In Progress",
            "13",
            now,
        ),
        _issue(
            organization.id,
            payment_sprint,
            "PAY-103",
            "Update checkout error states",
            by_number["EMP-1002"],
            "To Do",
            "To Do",
            "8",
            now,
        ),
        _issue(
            organization.id,
            payment_sprint,
            "PAY-104",
            "Automate regression pack",
            by_number["EMP-1003"],
            "Blocked",
            "In Progress",
            "5",
            now,
            blocked=True,
        ),
        _issue(
            organization.id,
            payment_sprint,
            "PAY-105",
            "Harden deployment rollback",
            by_number["EMP-1005"],
            "In Progress",
            "In Progress",
            "5",
            now,
            added=True,
        ),
        _issue(
            organization.id,
            payment_sprint,
            "PAY-106",
            "Investigate duplicate settlement",
            None,
            "To Do",
            "To Do",
            "3",
            now,
            priority="Highest",
        ),
    ]
    channel_issues = [
        _issue(
            organization.id,
            channel_sprint,
            "CHN-201",
            "Build onboarding shell",
            by_number["EMP-2002"],
            "Done",
            "Done",
            "8",
            now,
        ),
        _issue(
            organization.id,
            channel_sprint,
            "CHN-202",
            "Create customer eligibility API",
            by_number["EMP-2001"],
            "In Progress",
            "In Progress",
            "13",
            now,
        ),
        _issue(
            organization.id,
            channel_sprint,
            "CHN-203",
            "Complete accessibility review",
            by_number["EMP-2003"],
            "To Do",
            "To Do",
            "5",
            now,
        ),
        _issue(
            organization.id,
            channel_sprint,
            "CHN-204",
            "Document onboarding rules",
            by_number["EMP-2004"],
            "In Progress",
            "In Progress",
            "3",
            now,
        ),
    ]
    session.add_all(payment_issues + channel_issues)

    _add_start_snapshot(session, payment_sprint, payment_issues, now)
    _add_start_snapshot(session, channel_sprint, channel_issues, now)

    session.add_all(
        [
            IntegrationConfiguration(
                organization_id=organization.id,
                source=IntegrationSource.JIRA,
                name="demo-jira-cloud",
                configuration={"base_url": "https://example.atlassian.net", "site_id": "demo"},
                secret_reference="secret://capacity/demo/jira",  # noqa: S106
            ),
            IntegrationConfiguration(
                organization_id=organization.id,
                source=IntegrationSource.PAYSPACE,
                name="demo-payspace",
                configuration={"base_url": "https://api.example.payspace.com"},
                secret_reference="secret://capacity/demo/payspace",  # noqa: S106
            ),
            JiraFieldMapping(
                organization_id=organization.id,
                jira_site_id="demo",
                logical_field="story_points",
                jira_field_id="customfield_10016",
            ),
            IntegrationRun(
                organization_id=organization.id,
                source=IntegrationSource.JIRA,
                run_type="incremental",
                status=IntegrationRunStatus.SUCCEEDED,
                started_at=now - timedelta(minutes=20),
                completed_at=now - timedelta(minutes=15),
                records_read=len(payment_issues) + len(channel_issues),
                records_written=len(payment_issues) + len(channel_issues),
            ),
            IntegrationRun(
                organization_id=organization.id,
                source=IntegrationSource.PAYSPACE,
                run_type="incremental",
                status=IntegrationRunStatus.SUCCEEDED,
                started_at=now - timedelta(minutes=35),
                completed_at=now - timedelta(minutes=30),
                records_read=len(employees) + 2,
                records_written=len(employees) + 2,
            ),
        ]
    )

    # A historical blocked item makes the reporting examples less perfectly tidy.
    session.add(
        JiraIssue(
            organization_id=organization.id,
            sprint_id=payment_history[-1].id,
            jira_site_id="demo",
            external_id="PAY-099",
            issue_key="PAY-099",
            summary="Previous sprint carry-over",
            assignee_employee_id=by_number["EMP-1002"].id,
            status="Done",
            status_category="Done",
            priority="Medium",
            issue_type="Story",
            story_points=Decimal("5"),
            completed_at=payment_history[-1].end_at,
            source_updated_at=payment_history[-1].end_at,
        )
    )
    return [payment_sprint.id, channel_sprint.id]


async def _ensure_data_science_workspace(
    session: AsyncSession, organization: Organization
) -> UUID:
    today = date.today()
    current_start = today - timedelta(days=today.weekday())
    current_end = current_start + timedelta(days=11)
    now = datetime.now(UTC)

    team = await session.scalar(
        select(Team).where(
            Team.organization_id == organization.id,
            Team.slug == "data-science",
        )
    )
    if team is None:
        team = Team(
            organization_id=organization.id,
            name="Data Science",
            slug="data-science",
            description="Machine learning, decision intelligence, and trusted data products.",
            department="Data & Analytics",
            timezone="Africa/Johannesburg",
            location_code="ZA",
            velocity_lookback=5,
            settings={"portfolio": "Technology"},
        )
        session.add(team)
        await session.flush()
    else:
        team.description = "Machine learning, decision intelligence, and trusted data products."
        team.department = "Data & Analytics"
        team.timezone = "Africa/Johannesburg"
        team.location_code = "ZA"
        team.settings = {**team.settings, "portfolio": "Technology"}

    existing_sprint_id = await session.scalar(
        select(Sprint.id).where(
            Sprint.team_id == team.id,
            Sprint.jira_sprint_id == "DS-SPRINT-CURRENT",
        )
    )
    if existing_sprint_id is not None:
        return existing_sprint_id

    employee_specs = [
        (
            "EMP-3001",
            "jira-maya",
            "maya.singh@example.com",
            "Dr. Maya Singh",
            "Data Science Lead",
        ),
        (
            "EMP-3002",
            "jira-lwazi",
            "lwazi.mbeki@example.com",
            "Lwazi Mbeki",
            "Data Scientist",
        ),
        (
            "EMP-3003",
            "jira-emily",
            "emily.steyn@example.com",
            "Emily Steyn",
            "Machine Learning Engineer",
        ),
        (
            "EMP-3004",
            "jira-kagiso",
            "kagiso.molefe@example.com",
            "Kagiso Molefe",
            "Data Engineer",
        ),
        (
            "EMP-3005",
            "jira-aisha",
            "aisha.khan@example.com",
            "Aisha Khan",
            "Analytics Engineer",
        ),
    ]
    employees = [
        Employee(
            organization_id=organization.id,
            payspace_employee_number=number,
            jira_account_id=account_id,
            corporate_email=email,
            full_name=full_name,
            role_name=role_name,
            department="Data & Analytics",
            location_code="ZA",
            contract_hours_per_day=Decimal("8"),
            fte_factor=Decimal("1"),
            source_updated_at=now - timedelta(minutes=20),
        )
        for number, account_id, email, full_name, role_name in employee_specs
    ]
    session.add_all(employees)
    await session.flush()
    by_number = {employee.payspace_employee_number: employee for employee in employees}
    manager = by_number["EMP-3001"]
    for employee in employees:
        if employee.id != manager.id:
            employee.manager_employee_id = manager.id

    allocations = [
        ("EMP-3001", Decimal("100"), True),
        ("EMP-3002", Decimal("100"), True),
        ("EMP-3003", Decimal("100"), True),
        ("EMP-3004", Decimal("100"), True),
        ("EMP-3005", Decimal("100"), False),
    ]
    membership_start = current_start - timedelta(days=140)
    for employee_number, allocation, critical in allocations:
        employee = by_number[employee_number]
        session.add(
            TeamMembership(
                team_id=team.id,
                employee_id=employee.id,
                allocation_percent=allocation,
                delivery_role=employee.role_name,
                critical_role=critical,
                start_date=membership_start,
            )
        )

    system_admin = await session.scalar(
        select(User).where(
            User.organization_id == organization.id,
            User.external_subject == "local-system-admin",
        )
    )
    for employee in employees:
        session.add(
            IdentityMapping(
                organization_id=organization.id,
                employee_id=employee.id,
                jira_account_id=employee.jira_account_id,
                payspace_employee_number=employee.payspace_employee_number,
                corporate_email=employee.corporate_email,
                status="verified",
                match_method="corporate_email",
                verified_by_user_id=system_admin.id if system_admin else None,
            )
        )

    session.add(
        LeaveRecord(
            employee_id=by_number["EMP-3002"].id,
            start_date=current_start + timedelta(days=7),
            end_date=current_start + timedelta(days=8),
            leave_type="Annual Leave",
            status="approved",
            source_reference_id="DEMO-LEAVE-3002",
            source_updated_at=now - timedelta(minutes=30),
        )
    )

    history = await _historical_sprints(
        session,
        team,
        current_start,
        [Decimal("28"), Decimal("32"), Decimal("35"), Decimal("34"), Decimal("39")],
        allocations,
        by_number,
    )
    sprint = Sprint(
        team_id=team.id,
        jira_sprint_id="DS-SPRINT-CURRENT",
        name="Data Science Current Sprint",
        state=SprintState.ACTIVE,
        start_at=_at(current_start),
        end_at=_at(current_end, 17),
        goal="Deploy reliable customer intelligence and model monitoring.",
        source_updated_at=now - timedelta(minutes=10),
    )
    session.add(sprint)
    await session.flush()

    issues = [
        _issue(
            organization.id,
            sprint,
            "DS-301",
            "Deploy customer lifetime value model",
            by_number["EMP-3001"],
            "Done",
            "Done",
            "8",
            now,
        ),
        _issue(
            organization.id,
            sprint,
            "DS-302",
            "Build churn prediction feature pipeline",
            by_number["EMP-3002"],
            "In Progress",
            "In Progress",
            "13",
            now,
        ),
        _issue(
            organization.id,
            sprint,
            "DS-303",
            "Automate model performance validation",
            by_number["EMP-3003"],
            "In Review",
            "In Progress",
            "8",
            now,
        ),
        _issue(
            organization.id,
            sprint,
            "DS-304",
            "Add data quality monitoring",
            by_number["EMP-3004"],
            "Blocked",
            "In Progress",
            "5",
            now,
            blocked=True,
        ),
        _issue(
            organization.id,
            sprint,
            "DS-305",
            "Publish executive metrics model",
            by_number["EMP-3005"],
            "To Do",
            "To Do",
            "5",
            now,
        ),
        _issue(
            organization.id,
            sprint,
            "DS-306",
            "Investigate production model drift",
            None,
            "To Do",
            "To Do",
            "3",
            now,
            priority="Highest",
        ),
    ]
    session.add_all(issues)
    _add_start_snapshot(session, sprint, issues, now)
    session.add(
        JiraIssue(
            organization_id=organization.id,
            sprint_id=history[-1].id,
            jira_site_id="demo",
            external_id="DS-299",
            issue_key="DS-299",
            summary="Productionize propensity scoring model",
            assignee_employee_id=by_number["EMP-3002"].id,
            status="Done",
            status_category="Done",
            priority="High",
            issue_type="Story",
            story_points=Decimal("8"),
            completed_at=history[-1].end_at,
            source_updated_at=history[-1].end_at,
        )
    )
    return sprint.id


async def _historical_sprints(
    session: AsyncSession,
    team: Team,
    current_start: date,
    completed_values: list[Decimal],
    allocations: list[tuple[str, Decimal, bool]],
    employees: dict[str | None, Employee],
) -> list[Sprint]:
    result: list[Sprint] = []
    for index, completed in enumerate(completed_values, start=5):
        start = current_start - timedelta(days=14 * (10 - index))
        end = start + timedelta(days=11)
        sprint = Sprint(
            team_id=team.id,
            jira_sprint_id=f"{team.slug.upper()}-{index}",
            name=f"{team.name} Sprint {index}",
            state=SprintState.CLOSED,
            start_at=_at(start),
            end_at=_at(end, 17),
            completed_at=_at(end, 17),
            goal=f"Historical delivery objective {index}",
            source_updated_at=_at(end, 17),
        )
        session.add(sprint)
        await session.flush()
        effective_days = Decimal("45") + Decimal(index % 3 * 3)
        committed = completed + Decimal("5")
        rate = (completed / effective_days).quantize(Decimal("0.0001"))
        session.add(
            TeamVelocityMetric(
                team_id=team.id,
                sprint_id=sprint.id,
                completed_story_points=completed,
                effective_person_days=effective_days,
                story_points_per_effective_day=rate,
            )
        )
        session.add(
            TeamCapacitySummary(
                sprint_id=sprint.id,
                calculated_at=_at(end, 18),
                available_hours=effective_days * Decimal("8"),
                effective_person_days=effective_days,
                leave_impact_hours=Decimal(index % 2 * 8),
                story_points_per_effective_day=rate,
                story_point_capacity=(effective_days * rate).quantize(Decimal("0.01")),
                committed_story_points=committed,
                added_story_points=Decimal(index % 2 * 3),
                removed_story_points=ZERO,
                completed_story_points=completed,
                in_progress_story_points=ZERO,
                remaining_story_points=committed - completed,
                utilization_percent=(committed / (effective_days * rate) * 100).quantize(
                    Decimal("0.01")
                ),
                risk_level="medium" if index % 2 else "healthy",
                inputs_fresh_as_of=_at(end, 18),
            )
        )
        for employee_number, allocation, _ in allocations:
            employee = employees[employee_number]
            net_hours = Decimal("48") * allocation / Decimal("100")
            session.add(
                EmployeeCapacitySnapshot(
                    sprint_id=sprint.id,
                    employee_id=employee.id,
                    calculated_at=_at(end, 18),
                    working_days=Decimal("10"),
                    gross_hours=Decimal("80") * allocation / Decimal("100"),
                    leave_hours=ZERO,
                    holiday_hours=ZERO,
                    ceremony_hours=Decimal("4") * allocation / Decimal("100"),
                    buffer_hours=Decimal("28") * allocation / Decimal("100"),
                    net_hours=net_hours,
                    effective_person_days=net_hours / Decimal("8"),
                    assigned_story_points=(completed / Decimal(len(allocations))).quantize(
                        Decimal("0.01")
                    ),
                    inputs={"seeded": True, "allocation_percent": str(allocation)},
                )
            )
        result.append(sprint)
    return result


def _issue(
    organization_id: UUID,
    sprint: Sprint,
    key: str,
    summary: str,
    assignee: Employee | None,
    status: str,
    status_category: str,
    story_points: str,
    now: datetime,
    *,
    blocked: bool = False,
    added: bool = False,
    priority: str = "High",
) -> JiraIssue:
    return JiraIssue(
        organization_id=organization_id,
        sprint_id=sprint.id,
        jira_site_id="demo",
        external_id=key,
        issue_key=key,
        summary=summary,
        assignee_employee_id=assignee.id if assignee else None,
        status=status,
        status_category=status_category,
        priority=priority,
        issue_type="Story",
        story_points=Decimal(story_points),
        blocked=blocked,
        blocked_since=sprint.start_at if blocked else None,
        flagged=blocked,
        added_to_sprint_at=(sprint.start_at + timedelta(days=2) if added else sprint.start_at),
        completed_at=now - timedelta(days=1) if status_category == "Done" else None,
        source_updated_at=now - timedelta(minutes=10),
        normalized_fields={"labels": ["demo"], "components": ["capacity-planning"]},
    )


def _add_start_snapshot(
    session: AsyncSession, sprint: Sprint, issues: list[JiraIssue], now: datetime
) -> None:
    committed = [
        issue
        for issue in issues
        if issue.added_to_sprint_at is not None and issue.added_to_sprint_at <= sprint.start_at
    ]
    session.add(
        SprintCommitmentSnapshot(
            sprint_id=sprint.id,
            snapshot_type=SnapshotType.START,
            captured_at=sprint.start_at,
            issue_ids=[issue.external_id for issue in committed],
            committed_story_points=sum((issue.story_points for issue in committed), start=ZERO),
            added_story_points=ZERO,
            removed_story_points=ZERO,
            completed_story_points=sum(
                (issue.story_points for issue in committed if issue.status_category == "Done"),
                start=ZERO,
            ),
        )
    )
