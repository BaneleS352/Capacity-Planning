from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0")
HUNDRED = Decimal("100")
HOURS_PRECISION = Decimal("0.01")
DAYS_PRECISION = Decimal("0.001")


def _hours(value: Decimal) -> Decimal:
    return value.quantize(HOURS_PRECISION, rounding=ROUND_HALF_UP)


def _days(value: Decimal) -> Decimal:
    return value.quantize(DAYS_PRECISION, rounding=ROUND_HALF_UP)


def working_dates(start: date, end: date, holidays: set[date]) -> list[date]:
    if end < start:
        raise ValueError("Sprint end date must not be before start date")
    result: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in holidays:
            result.append(current)
        current += timedelta(days=1)
    return result


@dataclass(frozen=True, slots=True)
class LeaveWindow:
    start_date: date
    end_date: date
    partial_day_hours: Decimal | None = None


@dataclass(frozen=True, slots=True)
class CapacityPolicy:
    ceremony_hours_per_sprint: Decimal = ZERO
    meeting_buffer_percent: Decimal = ZERO
    support_buffer_percent: Decimal = ZERO
    review_buffer_percent: Decimal = ZERO
    unplanned_buffer_percent: Decimal = ZERO

    @property
    def total_buffer_percent(self) -> Decimal:
        total = (
            self.meeting_buffer_percent
            + self.support_buffer_percent
            + self.review_buffer_percent
            + self.unplanned_buffer_percent
        )
        if total < ZERO or total > HUNDRED:
            raise ValueError("Combined capacity buffers must be between 0 and 100 percent")
        return total


@dataclass(frozen=True, slots=True)
class EmployeeCapacityInput:
    sprint_start: date
    sprint_end: date
    contract_hours_per_day: Decimal
    fte_factor: Decimal
    allocation_percent: Decimal
    holidays: frozenset[date]
    leave: tuple[LeaveWindow, ...]
    policy: CapacityPolicy


@dataclass(frozen=True, slots=True)
class EmployeeCapacityResult:
    working_days: Decimal
    gross_hours: Decimal
    leave_hours: Decimal
    holiday_hours: Decimal
    ceremony_hours: Decimal
    buffer_hours: Decimal
    net_hours: Decimal
    effective_person_days: Decimal


def calculate_employee_capacity(value: EmployeeCapacityInput) -> EmployeeCapacityResult:
    if value.contract_hours_per_day <= ZERO:
        raise ValueError("Contract hours per day must be positive")
    if value.fte_factor <= ZERO or value.fte_factor > Decimal("1"):
        raise ValueError("FTE factor must be greater than 0 and at most 1")
    if value.allocation_percent < ZERO or value.allocation_percent > HUNDRED:
        raise ValueError("Allocation percent must be between 0 and 100")

    all_weekdays = working_dates(value.sprint_start, value.sprint_end, set())
    available_dates = working_dates(value.sprint_start, value.sprint_end, set(value.holidays))
    holiday_days = len(all_weekdays) - len(available_dates)
    allocation = value.allocation_percent / HUNDRED
    daily_hours = value.contract_hours_per_day * value.fte_factor * allocation
    gross_hours = Decimal(len(available_dates)) * daily_hours

    leave_by_date: dict[date, Decimal] = {}
    available_set = set(available_dates)
    for leave in value.leave:
        if leave.end_date < leave.start_date:
            raise ValueError("Leave end date must not be before start date")
        current = max(leave.start_date, value.sprint_start)
        end = min(leave.end_date, value.sprint_end)
        while current <= end:
            if current in available_set:
                requested = leave.partial_day_hours or value.contract_hours_per_day
                adjusted = min(requested * value.fte_factor * allocation, daily_hours)
                leave_by_date[current] = min(
                    daily_hours, leave_by_date.get(current, ZERO) + adjusted
                )
            current += timedelta(days=1)

    leave_hours = sum(leave_by_date.values(), start=ZERO)
    after_leave = max(ZERO, gross_hours - leave_hours)
    ceremony_hours = min(
        after_leave, value.policy.ceremony_hours_per_sprint * value.fte_factor * allocation
    )
    buffer_base = max(ZERO, after_leave - ceremony_hours)
    buffer_hours = buffer_base * value.policy.total_buffer_percent / HUNDRED
    net_hours = max(ZERO, buffer_base - buffer_hours)
    denominator = value.contract_hours_per_day if value.contract_hours_per_day else Decimal("1")

    return EmployeeCapacityResult(
        working_days=_days(Decimal(len(available_dates))),
        gross_hours=_hours(gross_hours),
        leave_hours=_hours(leave_hours),
        holiday_hours=_hours(Decimal(holiday_days) * daily_hours),
        ceremony_hours=_hours(ceremony_hours),
        buffer_hours=_hours(buffer_hours),
        net_hours=_hours(net_hours),
        effective_person_days=_days(net_hours / denominator),
    )


def story_points_per_effective_day(
    history: list[tuple[Decimal, Decimal]],
) -> Decimal | None:
    completed = sum((item[0] for item in history), start=ZERO)
    person_days = sum((item[1] for item in history), start=ZERO)
    if completed < ZERO or person_days <= ZERO:
        return None
    return (completed / person_days).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_utilization(
    planned_story_points: Decimal, story_point_capacity: Decimal | None
) -> Decimal | None:
    if story_point_capacity is None or story_point_capacity <= ZERO:
        return None
    return (planned_story_points / story_point_capacity * HUNDRED).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
