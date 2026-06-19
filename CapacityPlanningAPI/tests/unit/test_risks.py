from decimal import Decimal

from app.domain.risks import RiskContext, RiskPolicy, RiskType, detect_risks


def test_risk_engine_emits_structured_actionable_signals() -> None:
    risks = detect_risks(
        RiskContext(
            utilization_percent=Decimal("118"),
            leave_impact_percent=Decimal("15"),
            critical_role_unavailable_percent=Decimal("40"),
            added_scope_percent=Decimal("25"),
            not_started_percent=Decimal("35"),
            sprint_progress_percent=Decimal("60"),
            blocked_issues_over_threshold=2,
            unassigned_high_priority_issues=1,
            stale_data_hours=Decimal("12"),
            recurring_carry_over_sprints=3,
            unresolved_mappings=2,
        ),
        RiskPolicy(),
    )
    types = {item.risk_type for item in risks}
    assert {
        RiskType.OVER_CAPACITY,
        RiskType.CRITICAL_ROLE_UNAVAILABLE,
        RiskType.SCOPE_CREEP,
        RiskType.LOW_COMPLETION_PROBABILITY,
        RiskType.BLOCKED_WORK,
        RiskType.UNASSIGNED_HIGH_PRIORITY_WORK,
        RiskType.DATA_STALENESS,
        RiskType.CARRY_OVER_PATTERN,
        RiskType.MAPPING_ERROR,
    } <= types
    assert all(item.recommendation for item in risks)
    assert len({item.fingerprint for item in risks}) == len(risks)


def test_healthy_context_has_no_risks() -> None:
    risks = detect_risks(
        RiskContext(
            utilization_percent=Decimal("85"),
            leave_impact_percent=Decimal("5"),
            critical_role_unavailable_percent=Decimal("0"),
            added_scope_percent=Decimal("0"),
            not_started_percent=Decimal("20"),
            sprint_progress_percent=Decimal("40"),
            blocked_issues_over_threshold=0,
            unassigned_high_priority_issues=0,
            stale_data_hours=Decimal("1"),
        ),
        RiskPolicy(),
    )
    assert risks == []
