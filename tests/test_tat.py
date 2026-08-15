from datetime import datetime

from app.services.tat.calculator import (
    calculate_tat_hours,
    calculate_tat_minutes,
)


def test_same_day_tat():
    start = datetime(2026, 8, 10, 9, 0)
    end = datetime(2026, 8, 10, 13, 0)

    assert calculate_tat_minutes(start, end) == 240
    assert calculate_tat_hours(start, end) == 4.0


def test_before_working_hours():
    start = datetime(2026, 8, 10, 6, 0)
    end = datetime(2026, 8, 10, 10, 0)

    assert calculate_tat_hours(start, end) == 2.0


def test_after_working_hours():
    start = datetime(2026, 8, 10, 15, 0)
    end = datetime(2026, 8, 10, 19, 0)

    assert calculate_tat_hours(start, end) == 2.0


def test_weekend_is_excluded():
    start = datetime(2026, 8, 7, 16, 0)
    end = datetime(2026, 8, 10, 10, 0)

    assert calculate_tat_hours(start, end) == 3.0


def test_multiple_working_days():
    start = datetime(2026, 8, 10, 8, 0)
    end = datetime(2026, 8, 12, 17, 0)

    assert calculate_tat_hours(start, end) == 27.0


def test_negative_tat():
    start = datetime(2026, 8, 12, 10, 0)
    end = datetime(2026, 8, 11, 10, 0)

    assert calculate_tat_minutes(start, end) == 0