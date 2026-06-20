"""Runtime configuration for the House Hunter Agent."""

import os
from pathlib import Path


ENV_FILE_PATH = Path(".env").resolve()


def load_env_file(path=ENV_FILE_PATH):
    """Load simple KEY=value pairs from a local .env file."""
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/house_hunter.db"))

GMAIL_LABELS = [
    "house-hunter-casa.it",
    "house-hunter-immobiliare.it",
]
GMAIL_IMPORT_QUERY = (
    "label:house-hunter-casa.it OR label:house-hunter-immobiliare.it"
)

SEARCH_MODE = "purchase"
TARGET_AREA = "Roma Prati"
MAX_PRICE_EUR = 650000
IDEAL_PRICE_EUR = 500000
MIN_SIZE_SQM = 55
IDEAL_SIZE_SQM = 75
MIN_ROOMS = 2

MAX_DIGEST_ITEMS = 8

NOTIFY_WHEN_NO_CHANGES = False

WHATSAPP_ENABLED = os.getenv("HOUSE_HUNTER_WHATSAPP_ENABLED", "false").lower() == "true"
WHATSAPP_TO_NUMBER = os.getenv("HOUSE_HUNTER_WHATSAPP_TO", "")
META_WHATSAPP_ACCESS_TOKEN = os.getenv("META_WHATSAPP_ACCESS_TOKEN", "")
META_WHATSAPP_PHONE_NUMBER_ID = os.getenv("META_WHATSAPP_PHONE_NUMBER_ID", "")
META_WHATSAPP_API_VERSION = os.getenv("META_WHATSAPP_API_VERSION", "v23.0")
META_WHATSAPP_DAILY_TEMPLATE_NAME = os.getenv(
    "META_WHATSAPP_DAILY_TEMPLATE_NAME",
    "daily_house_hunter_update",
)
META_WHATSAPP_DAILY_TEMPLATE_LANGUAGE = os.getenv(
    "META_WHATSAPP_DAILY_TEMPLATE_LANGUAGE",
    "it",
)
META_WHATSAPP_DAILY_USE_TEMPLATE = (
    os.getenv("META_WHATSAPP_DAILY_USE_TEMPLATE", "false").lower() == "true"
)
META_WHATSAPP_DAILY_TEMPLATE_PARAM_COUNT = int(
    os.getenv("META_WHATSAPP_DAILY_TEMPLATE_PARAM_COUNT", "1")
)
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "change-me")
DAILY_RUN_SECRET = os.getenv("DAILY_RUN_SECRET", "change-me")
GMAIL_TOKEN_JSON = os.getenv("GMAIL_TOKEN_JSON", "")
