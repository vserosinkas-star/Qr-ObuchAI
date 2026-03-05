"""
QR-ОбучAI — Конфигурация проекта
Все чувствительные данные загружаются из переменных окружения (.env)
"""

import os
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Загружаем переменные из .env файла
load_dotenv()


# =============================================================================
# 🔐 GOOGLE WORKSPACE (Service Account)
# =============================================================================
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
GOOGLE_PRIVATE_KEY = os.getenv("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]


# =============================================================================
# 📊 GOOGLE SHEETS & DOCS IDs
# =============================================================================
SHEET_ID_REGISTRATIONS = os.getenv(
    "GOOGLE_SHEET_ID_REGISTRATIONS",
    "1BUjdLdJJeGHxnY1ZQ-XD0wbX0HlcZUCffIGF2gG56No"
)

SHEET_ID_REPORT = os.getenv(
    "GOOGLE_SHEET_ID_REPORT",
    "1ODZ7fu47zKnHy5XkHAvfkICXYy_1AuwHcI8DeSy6ooI"
)

SHEET_ID_MODULE_1 = os.getenv(
    "GOOGLE_SHEET_ID_MODULE_1",
    "16I9QEgnbca8thvII1TXSXOf4jUSX87t3yb2d1TbfdBk"
)

SHEET_ID_MODULE_2 = os.getenv(
    "GOOGLE_SHEET_ID_MODULE_2",
    "1UiGZ-FlTqsctDvPMKo1QKZwKgRANhQTwusrpf9m5qmY"
)

SHEET_ID_EPP = os.getenv(
    "GOOGLE_SHEET_ID_EPP",
    "1OdchPzlX1_VSv5wHlgM043TnNqnXiCfPX7wR3-X62II"
)

DOC_ID_ACT = os.getenv(
    "GOOGLE_DOC_ID_ACT",
    "1DAyOpwsYQJtBN6NDN4BzdXHrp56PyJT-tuWrsyQlPhY"
)


# =============================================================================
# 🤖 TELEGRAM BOT
# =============================================================================
BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "8455328792:AAHTDOXbDC7LzOwe8qY8Z1JgrQpOqsxhaDg"
)

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
COPY_CHAT_ID = os.getenv("COPY_CHAT_ID", "")


# =============================================================================
# 📧 EMAIL
# =============================================================================
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "vserosinkas@gmail.com")
SENDER_NAME = os.getenv("SENDER_NAME", "ЧОУ ДПО ГРАНИТ")
RECIPIENT_EMAILS = os.getenv(
    "RECIPIENT_EMAILS",
    "psnistor@sberbank.ru, zasypkin.dm.a@sberbank.ru"
)


# =============================================================================
# 🌍 GEOCODING
# =============================================================================
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_USER_AGENT = "QR-ObuchAI/1.0 (contact: vserosinkas@gmail.com)"


# =============================================================================
# 🏢 СПИСОК КИЦ (ГОРОДА)
# =============================================================================
DEFAULT_KIC_LIST: List[str] = [
    "Екатеринбург",
    "Нижний Тагил",
    "Асбест",
    "Первоуральск",
    "Каменск-Уральский",
    "Ирбит",
    "Серов",
    "Камышлов",
]


# =============================================================================
# 🏦 ГОСБ (Региональные отделения)
# =============================================================================
GOSB_CONFIG: Dict[str, Dict[str, str]] = {
    "ekb": {
        "name": "Аппарат Банка Екатеринбург",
        "sheet_registrations": "1BUjdLdJJeGHxnY1ZQ-XD0wbX0HlcZUCffIGF2gG56No",
        "sheet_report": "1ODZ7fu47zKnHy5XkHAvfkICXYy_1AuwHcI8DeSy6ooI",
    },
    "tyumen": {
        "name": "Тюменский ГОСБ Тюмень",
        "sheet_registrations": "1pF14w-l3Ij4_C4yS7WjaC52c2BiZwz4o6uOKsNcwZco",
        "sheet_report": "1rRLKl_7AF13oTkNl0zjdBMR4KlnsggjmxwPunx3hzuM",
    },
    "chel": {
        "name": "Челябинский ГОСБ Челябинск",
        "sheet_registrations": "13UWfwS25n9HihUntZQW6rIvwy-Tp2odnY41AaZ_i_Zc",
        "sheet_report": "1aSu1aCWZQ8RxUTV7_iusHRJ3h-prvKzLfU8lXAWYTJg",
    },
    "ugra": {
        "name": "Югорский ГОСБ Ханты-Мансийск",
        "sheet_registrations": "1de8M-j_1fNBGZnIUliYtvyhdp7rjM-AbkpZPMUEVCuI",
        "sheet_report": "13OuKRSO4jsNPAk5DkGVyhziz766F1IpgnYc7KIEMh7E",
    },
    "bash": {
        "name": "Башкирский ГОСБ Уфа",
        "sheet_registrations": "1I12HG4XZ7i-J1YstnyOFqgfqIz7Kf84hzD6PSQRKeeM",
        "sheet_report": "1fvJkTxcRrgJ8I0P22BlrjRPCP4HGnpJjd2ejyiL-a7E",
    },
    "kurgan": {
        "name": "Курганский ГОСБ Курган",
        "sheet_registrations": "1FHGnXPx8_pJ7CYP8IYfzQWgNr84ivf_DNqPtimvNT-c",
        "sheet_report": "1gAsFycltFWKjjc2ODyhwEvlZjjQ6BlMPLcqHJoYRCwc",
    },
}


# =============================================================================
# ⚙️ ПРИЛОЖЕНИЕ
# =============================================================================
APP_URL = os.getenv("APP_URL", "https://adresa-kic.vercel.app")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


# =============================================================================
# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================
def get_recipient_emails() -> List[str]:
    return [email.strip() for email in RECIPIENT_EMAILS.split(",")]


def validate_config() -> bool:
    required = ["BOT_TOKEN", "GOOGLE_SERVICE_ACCOUNT_EMAIL", "GOOGLE_PRIVATE_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print(f"⚠️ Отсутствуют переменные: {missing}")
        return False
    return True