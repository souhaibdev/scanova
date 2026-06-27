from dataclasses import dataclass, field


@dataclass
class Employee:
    uid: str
    cin: str
    full_name: str
    hourly_rate: float
    expected_start_time: str  # HH:MM
    cnss_enabled: bool = False
    cnss_value: float | None = None
    amo_enabled: bool = False
    amo_value: float | None = None

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "cin": self.cin,
            "full_name": self.full_name,
            "hourly_rate": self.hourly_rate,
            "expected_start_time": self.expected_start_time,
            "cnss_enabled": self.cnss_enabled,
            "cnss_value": self.cnss_value,
            "amo_enabled": self.amo_enabled,
            "amo_value": self.amo_value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Employee":
        cnss_value = data.get("cnss_value")
        amo_value = data.get("amo_value")
        return cls(
            uid=data["uid"],
            cin=data.get("cin", ""),
            full_name=data["full_name"],
            hourly_rate=float(data["hourly_rate"]),
            expected_start_time=data["expected_start_time"],
            cnss_enabled=bool(data.get("cnss_enabled", False)),
            cnss_value=float(cnss_value) if cnss_value not in (None, "") else None,
            amo_enabled=bool(data.get("amo_enabled", False)),
            amo_value=float(amo_value) if amo_value not in (None, "") else None,
        )
