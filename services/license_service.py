import logging

from translation_manager import TranslationManager
from utils.file_utils import load_json, save_json

logger = logging.getLogger(__name__)
translator = TranslationManager.instance()

ACTIVATION_CODE = "$scanova=20052006"
ACTIVATION_FILE = "activation.json"


def load_activation() -> dict:
    data = load_json(ACTIVATION_FILE)
    if isinstance(data, dict):
        return data
    return {}


def save_activation(activated: bool = True) -> dict:
    payload = {"activated": activated}
    save_json(ACTIVATION_FILE, payload)
    return payload


def is_activated() -> bool:
    return bool(load_activation().get("activated", False))


def activate(code: str) -> tuple[bool, str]:
    if code == ACTIVATION_CODE:
        save_activation(True)
        logger.info("Application activated successfully")
        return True, translator.t("activation.success")

    logger.warning("Invalid activation attempt")
    return False, translator.t("activation.invalid")
