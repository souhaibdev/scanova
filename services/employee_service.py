import logging
from typing import Optional

from models.employee import Employee
from utils.file_utils import load_json, save_json

logger = logging.getLogger(__name__)

EMPLOYEES_FILE = "employees.json"


def _load_all() -> dict[str, dict]:
    data = load_json(EMPLOYEES_FILE)
    if isinstance(data, list):
        # migrate old format
        result = {}
        for emp in data:
            result[emp["uid"]] = emp
        return result
    return data if data else {}


def _save_all(employees: dict[str, dict]):
    save_json(EMPLOYEES_FILE, employees)


def get_all_employees() -> list[Employee]:
    data = _load_all()
    return [Employee.from_dict(v) for v in data.values()]


def get_employee_by_uid(uid: str) -> Optional[Employee]:
    """Get employee by UID. Returns None if not found."""
    if not uid or not uid.strip():
        logger.warning("get_employee_by_uid called with empty/invalid UID: %r", uid)
        return None

    data = _load_all()
    if uid in data:
        employee_data = data[uid]
        logger.debug("Employee found for UID %s: %s", uid, employee_data.get('full_name', 'Unknown'))
        return Employee.from_dict(employee_data)

    logger.debug("No employee found for UID: %s", uid)
    return None


def add_employee(employee: Employee) -> tuple[bool, str]:
    data = _load_all()
    if employee.uid in data:
        return False, "Employee with this UID already exists."
    data[employee.uid] = employee.to_dict()
    _save_all(data)
    logger.info("Employee added: %s (%s)", employee.full_name, employee.uid)
    return True, "Employee added successfully."


def update_employee(employee: Employee) -> tuple[bool, str]:
    data = _load_all()
    if employee.uid not in data:
        return False, "Employee not found."
    data[employee.uid] = employee.to_dict()
    _save_all(data)
    logger.info("Employee updated: %s (%s)", employee.full_name, employee.uid)
    return True, "Employee updated successfully."


def delete_employee(uid: str) -> tuple[bool, str]:
    data = _load_all()
    if uid not in data:
        return False, "Employee not found."
    name = data[uid].get("full_name", uid)
    del data[uid]
    _save_all(data)
    logger.info("Employee deleted: %s (%s)", name, uid)
    return True, f"Employee '{name}' deleted."


def employee_count() -> int:
    return len(_load_all())
