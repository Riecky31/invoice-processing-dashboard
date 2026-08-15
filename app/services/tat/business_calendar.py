from datetime import date, datetime, time


WORK_START = time(8, 0)
WORK_END = time(17, 0)


def is_working_day(value: date | datetime) -> bool:

    if isinstance(value, datetime):
        value = value.date()

    return value.weekday() < 5


def workday_start(value: date | datetime) -> datetime:
  

    if isinstance(value, datetime):
        value = value.date()

    return datetime.combine(value, WORK_START)


def workday_end(value: date | datetime) -> datetime:
    """
    Return 17:00 on the supplied date.
    """

    if isinstance(value, datetime):
        value = value.date()

    return datetime.combine(value, WORK_END)