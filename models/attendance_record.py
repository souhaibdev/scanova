from dataclasses import dataclass
from typing import Optional


@dataclass
class AttendanceRecord:
    uid: str
    employee_name: str
    date: str           # YYYY-MM-DD
    entry_time: str     # HH:MM:SS
    exit_time: Optional[str] = None
    worked_hours: Optional[int] = None
    hourly_rate: Optional[float] = None
    total_salary: Optional[float] = None
    late: bool = False

    def to_row(self) -> list:
        return [
            self.uid,
            self.employee_name,
            self.date,
            self.entry_time,
            self.exit_time or "",
            self.worked_hours if self.worked_hours is not None else "",
            self.hourly_rate if self.hourly_rate is not None else "",
            self.total_salary if self.total_salary is not None else "",
            "YES" if self.late else "NO",
        ]

    @staticmethod
    def columns() -> list:
        return [
            "UID",
            "Employee Name",
            "Date",
            "Entry Time",
            "Exit Time",
            "Worked Hours",
            "Hourly Rate",
            "Total Salary",
            "Late",
        ]
