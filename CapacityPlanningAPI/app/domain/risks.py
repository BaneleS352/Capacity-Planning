import hashlib
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any


class RiskType(StrEnum):
    OVER_CAPACITY = "OVER_CAPACITY"
    UNDER_CAPACITY = "UNDER_CAPACITY"
    LEAVE_IMPACT = "LEAVE_IMPACT"
    CRITICAL_ROLE_UNAVAILABLE = "CRITICAL_ROLE_UNAVAILABLE"
    BLOCKED_WORK = "BLOCKED_WORK"
    SCOPE_CREEP = "SCOPE_CREEP"
    LOW_COMPLETION_PROBABILITY = "LOW_COMPLETION_PROBABILITY"
    UNASSIGNED_HIGH_PRIORITY_WORK = "UNASSIGNED_HIGH_PRIORITY_WORK"
    STALE_IN_PROGRESS = "STALE_IN_PROGRESS"
    CARRY_OVER_PATTERN = "CARRY_OVER_PATTERN"
    DATA_STALENESS = "DATA_STALENESS"
    MAPPING_ERROR = "MAPPING_ERROR"


class DomainSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    under_capacity_percent: Decimal = Decimal("70")
    watch_capacity_percent: Decimal = Decimal("95")
    over_capacity_percent: Decimal = Decimal("110")
    critical_role_unavailable_percent: Decimal = Decimal("25")
    scope_change_percent: Decimal = Decimal("20")
    not_started_percent: Decimal = Decimal("30")
    blocked_working_days: int = 2
    stale_data_hours: int = 8


@dataclass(frozen=True, slots=True)
class RiskContext:
    utilization_percent: Decimal | None
    leave_impact_percent: Decimal
    critical_role_unavailable_percent: Decimal
    added_scope_percent: Decimal
    not_started_percent: Decimal
    sprint_progress_percent: Decimal
    blocked_issues_over_threshold: int
    unassigned_high_priority_issues: int
    stale_data_hours: Decimal | None
    recurring_carry_over_sprints: int = 0
    unresolved_mappings: int = 0


@dataclass(frozen=True, slots=True)
class DomainRisk:
    risk_type: RiskType
    severity: DomainSeverity
    message: str
    recommendation: str
    context: dict[str, Any]

    @property
    def fingerprint(self) -> str:
        stable = f"{self.risk_type}:{sorted(self.context.items())}"
        return hashlib.sha256(stable.encode()).hexdigest()


def detect_risks(context: RiskContext, policy: RiskPolicy) -> list[DomainRisk]:
    risks: list[DomainRisk] = []
    utilization = context.utilization_percent
    if utilization is not None and utilization > policy.over_capacity_percent:
        risks.append(
            DomainRisk(
                RiskType.OVER_CAPACITY,
                DomainSeverity.HIGH,
                f"Team utilization is {utilization}% of adjusted capacity.",
                "Remove scope, add capacity, or explicitly accept the delivery risk.",
                {"utilization_percent": str(utilization)},
            )
        )
    elif utilization is not None and utilization > policy.watch_capacity_percent:
        risks.append(
            DomainRisk(
                RiskType.OVER_CAPACITY,
                DomainSeverity.MEDIUM,
                f"Team utilization is {utilization}% and is above the healthy range.",
                "Review scope and capacity before committing the sprint.",
                {"utilization_percent": str(utilization)},
            )
        )
    elif utilization is not None and utilization < policy.under_capacity_percent:
        risks.append(
            DomainRisk(
                RiskType.UNDER_CAPACITY,
                DomainSeverity.LOW,
                f"Team utilization is {utilization}% and may indicate under-planning.",
                "Confirm backlog readiness and non-Jira obligations before adding scope.",
                {"utilization_percent": str(utilization)},
            )
        )

    if context.critical_role_unavailable_percent > policy.critical_role_unavailable_percent:
        risks.append(
            DomainRisk(
                RiskType.CRITICAL_ROLE_UNAVAILABLE,
                DomainSeverity.HIGH,
                "A critical role is unavailable for a material part of the sprint.",
                "Adjust the plan or arrange qualified coverage.",
                {"unavailable_percent": str(context.critical_role_unavailable_percent)},
            )
        )
    elif context.leave_impact_percent > policy.critical_role_unavailable_percent:
        risks.append(
            DomainRisk(
                RiskType.LEAVE_IMPACT,
                DomainSeverity.MEDIUM,
                f"Leave removes {context.leave_impact_percent}% of gross team capacity.",
                "Review role coverage and reduce sprint scope where necessary.",
                {"leave_impact_percent": str(context.leave_impact_percent)},
            )
        )

    if context.added_scope_percent > policy.scope_change_percent:
        risks.append(
            DomainRisk(
                RiskType.SCOPE_CREEP,
                DomainSeverity.HIGH,
                f"{context.added_scope_percent}% of sprint scope was added after sprint start.",
                "Review scope changes and re-confirm the sprint commitment.",
                {"added_scope_percent": str(context.added_scope_percent)},
            )
        )
    if (
        context.sprint_progress_percent >= Decimal("50")
        and context.not_started_percent > policy.not_started_percent
    ):
        risks.append(
            DomainRisk(
                RiskType.LOW_COMPLETION_PROBABILITY,
                DomainSeverity.HIGH,
                f"{context.not_started_percent}% of work is not started after sprint midpoint.",
                "Re-plan remaining work and address blockers immediately.",
                {"not_started_percent": str(context.not_started_percent)},
            )
        )
    if context.blocked_issues_over_threshold:
        risks.append(
            DomainRisk(
                RiskType.BLOCKED_WORK,
                DomainSeverity.HIGH,
                f"{context.blocked_issues_over_threshold} issue(s) have been blocked too long.",
                "Escalate dependencies and assign an owner for each blocker.",
                {"issue_count": context.blocked_issues_over_threshold},
            )
        )
    if context.unassigned_high_priority_issues:
        risks.append(
            DomainRisk(
                RiskType.UNASSIGNED_HIGH_PRIORITY_WORK,
                DomainSeverity.MEDIUM,
                f"{context.unassigned_high_priority_issues} high-priority issue(s) are unassigned.",
                "Assign ownership or remove the issues from the sprint commitment.",
                {"issue_count": context.unassigned_high_priority_issues},
            )
        )
    if context.stale_data_hours is not None and context.stale_data_hours > policy.stale_data_hours:
        risks.append(
            DomainRisk(
                RiskType.DATA_STALENESS,
                DomainSeverity.MEDIUM,
                f"Source data is {context.stale_data_hours} hours old.",
                "Reconcile the source before making a final planning decision.",
                {"stale_data_hours": str(context.stale_data_hours)},
            )
        )
    if context.recurring_carry_over_sprints >= 3:
        risks.append(
            DomainRisk(
                RiskType.CARRY_OVER_PATTERN,
                DomainSeverity.MEDIUM,
                "The team has carried work over for at least three consecutive sprints.",
                "Review estimation, dependencies, interruptions, and commitment policy.",
                {"consecutive_sprints": context.recurring_carry_over_sprints},
            )
        )
    if context.unresolved_mappings:
        risks.append(
            DomainRisk(
                RiskType.MAPPING_ERROR,
                DomainSeverity.MEDIUM,
                f"{context.unresolved_mappings} identity mapping(s) remain unresolved.",
                "Resolve Jira-to-PaySpace identities before relying on employee capacity.",
                {"mapping_count": context.unresolved_mappings},
            )
        )
    return risks
