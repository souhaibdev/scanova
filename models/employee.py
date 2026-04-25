from dataclasses import dataclass, field


@dataclass
class Employee:
    uid: str
    full_name: str
    hourly_rate: float
    expected_start_time: str  # HH:MM

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "full_name": self.full_name,
            "hourly_rate": self.hourly_rate,
            "expected_start_time": self.expected_start_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Employee":
        return cls(
            uid=data["uid"],
            full_name=data["full_name"],
            hourly_rate=float(data["hourly_rate"]),
            expected_start_time=data["expected_start_time"],
        )
