import os
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

# =============================================================================
# 🔐 GOOGLE WORKSPACE
# =============================================================================
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
GOOGLE_PRIVATE_KEY = os.getenv("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]

# =============================================================================
# 🤖 TELEGRAM
# =============================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

# =============================================================================
# 🏦 КОНФИГУРАЦИЯ ГОСБ
# =============================================================================
GOSB_CONFIG: Dict[str, Dict] = {
    'ekb': {
        'name': 'Аппарат Банка Екатеринбург',
        'sheet_id': os.getenv("SHEET_ID_EKB", "1BUjdLdJJeGHxnY1ZQ-XD0wbX0HlcZUCffIGF2gG56No"),
        'cities': ['Екатеринбург', 'Нижний Тагил', 'Асбест', 'Первоуральск', 'Каменск-Уральский', 'Ирбит', 'Серов', 'Камышлов'],
    },
    'tyumen': {
        'name': 'Тюменский ГОСБ',
        'sheet_id': os.getenv("SHEET_ID_TYUMEN", "1pF14w-l3Ij4_C4yS7WjaC52c2BiZwz4o6uOKsNcwZco"),
        'cities': ['Тюмень', 'Тобольск', 'Сургут', 'Нижневартовск', 'Нефтеюганск'],
    },
    'chel': {
        'name': 'Челябинский ГОСБ',
        'sheet_id': os.getenv("SHEET_ID_CHEL", "13UWfwS25n9HihUntZQW6rIvwy-Tp2odnY41AaZ_i_Zc"),
        'cities': ['Челябинск', 'Магнитогорск', 'Златоуст', 'Миасс', 'Копейск'],
    },
    'ugra': {
        'name': 'Югорский ГОСБ',
        'sheet_id': os.getenv("SHEET_ID_UGRA", "1de8M-j_1fNBGZnIUliYtvyhdp7rjM-AbkpZPMUEVCuI"),
        'cities': ['Ханты-Мансийск', 'Сургут', 'Нижневартовск', 'Нефтеюганск', 'Нягань'],
    },
    'bash': {
        'name': 'Башкирский ГОСБ',
        'sheet_id': os.getenv("SHEET_ID_BASH", "1I12HG4XZ7i-J1YstnyOFqgfqIz7Kf84hzD6PSQRKeeM"),
        'cities': ['Уфа', 'Стерлитамак', 'Салават', 'Нефтекамск', 'Октябрьский'],
    },
    'kurgan': {
        'name': 'Курганский ГОСБ',
        'sheet_id': os.getenv("SHEET_ID_KURGAN", "1FHGnXPx8_pJ7CYP8IYfzQWgNr84ivf_DNqPtimvNT-c"),
        'cities': ['Курган', 'Шадринск', 'Катайск', 'Щучье', 'Макушино'],
    },
}

# =============================================================================
# 🌍 GEOCODING
# =============================================================================
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_USER_AGENT = "QR-ObuchAI/1.0"

# =============================================================================
#  TIMEZONE
# =============================================================================
def get_yekaterinburg_time():
    """Возвращает текущее время Екатеринбурга (UTC+5)"""
    from datetime import datetime, timedelta
    return datetime.utcnow() + timedelta(hours=5)

# =============================================================================
# 🔧 UTILS
# =============================================================================
def validate_config() -> bool:
    required = ["BOT_TOKEN", "GOOGLE_SERVICE_ACCOUNT_EMAIL", "GOOGLE_PRIVATE_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print(f"⚠️ Missing env vars: {missing}")
        return False
    return True
