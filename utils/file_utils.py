import json
import os
import logging

import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
IMAGES_DIR = os.path.join(BASE_DIR, "images")


def ensure_directories():
    """Create all required directories if they do not exist."""
    for d in (DATA_DIR, LOGS_DIR, IMAGES_DIR):
        os.makedirs(d, exist_ok=True)
    logger.info("Directories verified.")


def json_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def xlsx_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def load_json(filename: str) -> dict | list:
    path = json_path(filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    path = json_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_xlsx(filename: str, columns: list) -> pd.DataFrame:
    path = xlsx_path(filename)
    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_excel(path, index=False, engine="openpyxl")
        return df
    try:
        return pd.read_excel(path, dtype=str, engine="openpyxl")
    except Exception as e:
        logger.warning("Error reading %s: %s. Creating new file.", filename, e)
        df = pd.DataFrame(columns=columns)
        df.to_excel(path, index=False, engine="openpyxl")
        return df


def save_xlsx(filename: str, df: pd.DataFrame):
    path = xlsx_path(filename)
    df.to_excel(path, index=False, engine="openpyxl")
    # Ensure file is written and closed
    import time
    time.sleep(0.01)  # Small delay to ensure I/O completion


def setup_logging():
    ensure_directories()
    log_file = os.path.join(LOGS_DIR, "system.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger.info("Logging initialized.")
