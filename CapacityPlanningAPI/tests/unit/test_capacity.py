from datetime import date
from decimal import Decimal

import pytest

from app.domain.capacity import (
    CapacityPolicy,
    EmployeeCapacityInput,
    LeaveWindow,
    calculate_employee_capacity,
    calculate_utilization,
    story_points_per_effective_day,
    working_dates,
)


def test_capacity_deducts_holiday_leave_ceremony_and_buffers_once() -> None:
    result = calculate_employee_capacity(
        EmployeeCapacityInput(
            sprint_start=date(2026, 6, 1),
            sprint_end=date(2026, 6, 12),
            contract_hours_per_day=Decimal("8"),
            fte_factor=Decimal("1"),
            allocation_percent=Decimal("100"),
            holidays=frozenset({date(2026, 6, 5)}),
            leave=(LeaveWindow(date(2026, 6, 8), date(2026, 6, 9)),),
            policy=CapacityPolicy(
                ceremony_hours_per_sprint=Decimal("4"),
                meeting_buffer_percent=Decimal("10"),
                unplanned_buffer_percent=Decimal("10"),
            ),
        )
    )

    assert result.working_days == Decimal("9.000")
    assert result.gross_hours == Decimal("72.00")
    assert result.holiday_hours == Decimal("8.00")
    assert result.leave_hours == Decimal("16.00")
    assert result.ceremony_hours == Decimal("4.00")
    assert result.buffer_hours == Decimal("10.40")
    assert result.net_hours == Decimal("41.60")
    assert result.effective_person_days == Decimal("5.200")


def test_overlapping_leave_is_capped_at_daily_capacity() -> None:
    result = calculate_employee_capacity(
        EmployeeCapacityInput(
            sprint_start=date(2026, 6, 1),
            sprint_end=date(2026, 6, 1),
            contract_hours_per_day=Decimal("8"),
            fte_factor=Decimal("1"),
            allocation_percent=Decimal("50"),
            holidays=frozenset(),
            leave=(
                LeaveWindow(date(2026, 6, 1), date(2026, 6, 1), Decimal("6")),
                LeaveWindow(date(2026, 6, 1), date(2026, 6, 1), Decimal("6")),
            ),
            policy=CapacityPolicy(),
        )
    )
    assert result.gross_hours == Decimal("4.00")
    assert result.leave_hours == Decimal("4.00")
    assert result.net_hours == Decimal("0.00")


def test_velocity_and_utilization_are_team_level_ratios() -> None:
    ratio = story_points_per_effective_day(
        [(Decimal("30"), Decimal("10")), (Decimal("24"), Decimal("8"))]
    )
    assert ratio == Decimal("3.0000")
    assert calculate_utilization(Decimal("66"), Decimal("60")) == Decimal("110.00")
    assert calculate_utilization(Decimal("10"), None) is None


def test_invalid_dates_and_buffers_fail_fast() -> None:
    with pytest.raises(ValueError, match="end date"):
        working_dates(date(2026, 6, 2), date(2026, 6, 1), set())
    with pytest.raises(ValueError, match="buffers"):
        _ = CapacityPolicy(
            meeting_buffer_percent=Decimal("60"), support_buffer_percent=Decimal("50")
        ).total_buffer_percent
