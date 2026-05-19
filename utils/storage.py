import os

BASE_DIR = os.path.join(os.getenv("APPDATA"), "Scanova")
os.makedirs(BASE_DIR, exist_ok=True)

DATA_FILE = os.path.join(BASE_DIR, "data.json")