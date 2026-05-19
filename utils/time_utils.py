from datetime import datetime, timedelta
import math


def now_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_time_str() -> str:
    return datetime.now().strftime("%H:%M")


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


def calc_worked_hours(entry_str: str, exit_str: str) -> float:
    """Return the worked hours between entry and exit as decimal hours."""
    entry = parse_time(entry_str)
    exit_ = parse_time(exit_str)
    delta = exit_ - entry
    if delta.total_seconds() < 0:
        delta += timedelta(days=1)
    hours = delta.total_seconds() / 3600
    return round(hours, 2)


def is_late(entry_str: str, expected_start: str, grace_minutes: int = 15) -> bool:
    """Return True if entry is more than grace_minutes after expected start.
    
    Example: expected_start=08:00, grace=15 → late only if entry > 08:15
    """
    entry = parse_time(entry_str)
    expected = parse_time(expected_start)
    return (entry - expected).total_seconds() > grace_minutes * 60


def minutes_between(start_str: str, end_str: str) -> int:
    """Return number of full minutes between two time strings."""
    start = parse_time(start_str)
    end = parse_time(end_str)
    delta = end - start
    if delta.total_seconds() < 0:
        delta += timedelta(days=1)
    return int(delta.total_seconds() // 60)