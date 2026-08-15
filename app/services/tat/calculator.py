from datetime import datetime, timedelta

from app.services.tat.business_calendar import (
    WORK_END,
    WORK_START,
    is_working_day,
    workday_end,
    workday_start,
)


def calculate_tat_minutes(
    start: datetime,
    end: datetime,
) -> int:
  
    if start is None or end is None:
        return 0

    if end <= start:
        return 0

    total_minutes = 0
    current_date = start.date()
    end_date = end.date()

    while current_date <= end_date:

        if not is_working_day(current_date):
            current_date += timedelta(days=1)
            continue

        day_start = workday_start(current_date)
        day_end = workday_end(current_date)

        period_start = max(start, day_start)
        period_end = min(end, day_end)

        if period_end > period_start:
            total_minutes += int(
                (period_end - period_start).total_seconds() / 60
            )

        current_date += timedelta(days=1)

    return total_minutes


def calculate_tat_hours(
    start: datetime,
    end: datetime,
) -> float:
    """
    Return TAT as decimal working hours.
    """

    minutes = calculate_tat_minutes(start, end)

    return round(minutes / 60, 2)