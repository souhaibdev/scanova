from datetime import datetime, timedelta
import math


def now_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def now_datetime_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def parse_time(time_str: str) -> datetime:
    """Parse HH:MM or HH:MM:SS into a datetime (date part is today)."""
    today = datetime.now().date()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(time_str, fmt).time()
            return datetime.combine(today, t)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse time: {time_str}")


def calc_worked_hours(entry_str: str, exit_str: str) -> int:
    """Return floored full hours between entry and exit."""
    entry = parse_time(entry_str)
    exit_ = parse_time(exit_str)
    delta = exit_ - entry
    if delta.total_seconds() < 0:
        delta += timedelta(days=1)
    return int(math.floor(delta.total_seconds() / 3600))


def is_late(entry_str: str, expected_start: str) -> bool:
    """Return True if entry is after expected start."""
    entry = parse_time(entry_str)
    expected = parse_time(expected_start)
    return entry > expected
