import hashlib
import logging

from translation_manager import TranslationManager
from utils.file_utils import load_json, save_json
from utils.storage import CREDENTIALS_FILE

logger = logging.getLogger(__name__)
_translator = TranslationManager.instance()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_first_launch() -> bool:
    creds = load_json(CREDENTIALS_FILE)
    return not bool(creds)


def register_admin(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, _translator.t("auth.username_password_required")
    if len(password) < 6:
        return False, _translator.t("auth.password_too_short")
    creds = load_json(CREDENTIALS_FILE)
    if creds:
        return False, _translator.t("auth.admin_already_registered")
    creds = {
        "username": username,
        "password_hash": _hash_password(password),
    }
    save_json(CREDENTIALS_FILE, creds)
    logger.info("Admin registered: %s", username)
    return True, _translator.t("auth.admin_registered_successfully")


def login(username: str, password: str) -> tuple[bool, str]:
    creds = load_json(CREDENTIALS_FILE)
    if not creds:
        return False, _translator.t("auth.no_admin_registered")
    if creds.get("username") != username:
        return False, _translator.t("auth.invalid_username")
    if creds.get("password_hash") != _hash_password(password):
        return False, _translator.t("auth.invalid_password")
    logger.info("Login successful: %s", username)
    return True, _translator.t("auth.login_successful")


def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    creds = load_json(CREDENTIALS_FILE)
    if not creds:
        return False, _translator.t("auth.no_admin_registered")
    if creds.get("username") != username:
        return False, _translator.t("auth.invalid_username")
    if creds.get("password_hash") != _hash_password(old_password):
        return False, _translator.t("auth.old_password_incorrect")
    if len(new_password) < 6:
        return False, _translator.t("auth.new_password_too_short")
    creds["password_hash"] = _hash_password(new_password)
    save_json(CREDENTIALS_FILE, creds)
    logger.info("Password changed for: %s", username)
    return True, _translator.t("auth.password_changed_successfully")
