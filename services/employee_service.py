import logging
from typing import Optional

from translation_manager import TranslationManager
from models.employee import Employee
from translation_manager import TranslationManager
from utils.file_utils import load_json, save_json
from utils.storage import EMPLOYEES_FILE

logger = logging.getLogger(__name__)
_translator = TranslationManager.instance()


def _load_all() -> dict[str, dict]:
    data = load_json(EMPLOYEES_FILE)
    if isinstance(data, list):
        result = {}
        for emp in data:
            result[emp["uid"]] = emp
        return result
    return data if data else {}


def _save_all(employees: dict[str, dict]) -> None:
    save_json(EMPLOYEES_FILE, employees)


def get_all_employees() -> list[Employee]:
    data = _load_all()
    return [Employee.from_dict(v) for v in data.values()]


def get_employee_by_uid(uid: str) -> Optional[Employee]:
    if not uid or not uid.strip():
        logger.warning("get_employee_by_uid called with empty/invalid UID: %r", uid)
        return None

    data = _load_all()
    employee_data = data.get(uid)
    if employee_data:
        emp = Employee.from_dict(employee_data)
        logger.debug(
            "Employee found for UID %s: %s | CNSS: enabled=%s, value=%s | AMO: enabled=%s, value=%s",
            uid, emp.full_name, emp.cnss_enabled, emp.cnss_value, emp.amo_enabled, emp.amo_value
        )
        return emp

    logger.debug("No employee found for UID: %s", uid)
    return None


def add_employee(employee: Employee) -> tuple[bool, str]:
    if not employee.uid or not employee.uid.strip():
        return False, _translator.t("service.employee_uid_required")

    data = _load_all()
    if employee.uid in data:
        return False, _translator.t("service.employee_uid_exists")

    emp_dict = employee.to_dict()
    logger.debug(
        "Adding employee: %s (%s) with CNSS: enabled=%s, value=%s | AMO: enabled=%s, value=%s",
        employee.full_name, employee.uid, employee.cnss_enabled, employee.cnss_value,
        employee.amo_enabled, employee.amo_value
    )
    data[employee.uid] = emp_dict
    _save_all(data)
    logger.info("Employee added: %s (%s)", employee.full_name, employee.uid)
    return True, _translator.t("service.employee_added")


def update_employee(employee: Employee) -> tuple[bool, str]:
    if not employee.uid or not employee.uid.strip():
        return False, _translator.t("service.employee_uid_required")

    data = _load_all()
    if employee.uid not in data:
        return False, _translator.t("service.employee_not_found")

    emp_dict = employee.to_dict()
    logger.debug(
        "Updating employee: %s (%s) with CNSS: enabled=%s, value=%s | AMO: enabled=%s, value=%s",
        employee.full_name, employee.uid, employee.cnss_enabled, employee.cnss_value,
        employee.amo_enabled, employee.amo_value
    )
    data[employee.uid] = emp_dict
    _save_all(data)
    logger.info("Employee updated: %s (%s)", employee.full_name, employee.uid)
    return True, _translator.t("service.employee_updated")


def delete_employee(uid: str) -> tuple[bool, str]:
    if not uid or not uid.strip():
        return False, _translator.t("service.employee_uid_required")

    data = _load_all()
    if uid not in data:
        return False, _translator.t("service.employee_not_found")

    name = data[uid].get("full_name", uid)
    del data[uid]
    _save_all(data)
    logger.info("Employee deleted: %s (%s)", name, uid)
    return True, _translator.t("service.employee_deleted", name=name)


def get_employees_by_cin(cin: str) -> list[Employee]:
    if not cin or not cin.strip():
        logger.warning("get_employees_by_cin called with empty CIN")
        return []

    cin = cin.strip().upper()
    data = _load_all()
    results = [
        Employee.from_dict(v)
        for v in data.values()
        if v.get("cin", "").upper() == cin
    ]
    logger.debug("Found %d employee(s) with CIN %s", len(results), cin)
    return results


def employee_count() -> int:
    return len(_load_all())