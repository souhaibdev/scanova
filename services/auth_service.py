import hashlib
import logging
import os

from utils.file_utils import load_json, save_json

logger = logging.getLogger(__name__)

CREDENTIALS_FILE = "credentials.json"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_first_launch() -> bool:
    creds = load_json(CREDENTIALS_FILE)
    return not bool(creds)


def register_admin(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    creds = load_json(CREDENTIALS_FILE)
    if creds:
        return False, "Admin already registered."
    creds = {
        "username": username,
        "password_hash": _hash_password(password),
    }
    save_json(CREDENTIALS_FILE, creds)
    logger.info("Admin registered: %s", username)
    return True, "Admin registered successfully."


def login(username: str, password: str) -> tuple[bool, str]:
    creds = load_json(CREDENTIALS_FILE)
    if not creds:
        return False, "No admin registered yet."
    if creds.get("username") != username:
        return False, "Invalid username."
    if creds.get("password_hash") != _hash_password(password):
        return False, "Invalid password."
    logger.info("Login successful: %s", username)
    return True, "Login successful."


def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    creds = load_json(CREDENTIALS_FILE)
    if not creds:
        return False, "No admin registered."
    if creds.get("username") != username:
        return False, "Invalid username."
    if creds.get("password_hash") != _hash_password(old_password):
        return False, "Old password incorrect."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."
    creds["password_hash"] = _hash_password(new_password)
    save_json(CREDENTIALS_FILE, creds)
    logger.info("Password changed for: %s", username)
    return True, "Password changed successfully."
