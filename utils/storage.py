import os

APPDATA_DIR = os.getenv("APPDATA") or os.path.expanduser("~")
BASE_DIR = os.path.join(APPDATA_DIR, "Scanova")
os.makedirs(BASE_DIR, exist_ok=True)

EMPLOYEES_FILE = os.path.join(BASE_DIR, "employees.json")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance.xlsx")
ADVANCES_FILE = os.path.join(BASE_DIR, "advances.xlsx")
PRIMES_FILE = os.path.join(BASE_DIR, "primes.xlsx")
NOTES_FILE = os.path.join(BASE_DIR, "notes.xlsx")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
IMAGES_DIR = os.path.join(BASE_DIR, "images")