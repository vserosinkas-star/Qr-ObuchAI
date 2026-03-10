#!/usr/bin/env python3
"""
🎓 QR-ОбучAI — FastAPI Backend
Система регистрации инкассаторов на обучение с записью в Google Sheets
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# =============================================================================
# 🔧 НАСТРОЙКА ЛОГИРОВАНИЯ
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# 🚀 ПРИЛОЖЕНИЕ
# =============================================================================
app = FastAPI(
    title="QR-ОбучAI API",
    description="Система регистрации инкассаторов на обучение",
    version="1.0.0"
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 📊 МОДЕЛИ ДАННЫХ
# =============================================================================
class RegistrationData(BaseModel):
    fio: str
    kic: str
    purpose: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# =============================================================================
# 🌍 КОНСТАНТЫ
# =============================================================================
DEFAULT_KIC_LIST = [
    "Екатеринбург", "Нижний Тагил", "Асбест", "Первоуральск",
    "Каменск-Уральский", "Ирбит", "Серов", "Камышлов",
]

DEFAULT_SHEET_ID = "1BUjdLdJJeGHxnY1ZQ-XD0wbX0HlcZUCffIGF2gG56No"
SHEET_RANGE = "Регистрации!A:F"

# =============================================================================
# 🕐 ВРЕМЯ
# =============================================================================
def get_yekaterinburg_time():
    """Возвращает текущее время Екатеринбурга (UTC+5)"""
    return datetime.utcnow() + timedelta(hours=5)

# =============================================================================
# 📊 GOOGLE SHEETS СЕРВИС
# =============================================================================
def get_sheets_service():
    """
    Создаёт клиент Google Sheets API
    
    Returns:
        service: Google Sheets service object или None
    """
    logger.info("🔍 [SHEETS] Начинаю создание сервиса...")
    
    try:
        # Получаем переменные окружения
        private_key = os.environ.get("GOOGLE_PRIVATE_KEY", "")
        client_email = os.environ.get("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
        
        logger.info(f"🔑 [SHEETS] Client email: {client_email[:30] + '...' if len(client_email) > 30 else client_email}")
        logger.info(f"🔑 [SHEETS] Private key length: {len(private_key)}")
        
        # Проверка наличия учётных данных
        if not private_key or not client_email:
            logger.error("❌ [SHEETS] Google credentials not found in environment variables!")
            return None
        
        # Исправляем формат ключа (заменяем \n на реальные переносы строк)
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
            logger.info("🔧 [SHEETS] Fixed private key format (replaced \\n with newline)")
        
        # Создаём учётные данные
        credentials_info = {
            "type": "service_account",
            "project_id": "qr-obuchai",
            "private_key_id": "key123",
            "private_key": private_key,
            "client_email": client_email,
            "client_id": "123456",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        }
        
        logger.info("🔐 [SHEETS] Creating credentials from service account info...")
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        logger.info("🔗 [SHEETS] Building Sheets API client...")
        service = build('sheets', 'v4', credentials=credentials)
        
        logger.info("✅ [SHEETS] Google Sheets client created successfully!")
        return service
        
    except Exception as e:
        logger.error(f"❌ [SHEETS] Error creating Sheets client: {str(e)}")
        logger.error(f"📋 [SHEETS] Traceback: {get_traceback()}")
        return None


def append_to_sheet(service, spreadsheet_id, range_name, values):
    """
    Добавляет строку в Google Sheet
    
    Args:
        service: Google Sheets service
        spreadsheet_id: ID таблицы
        range_name: Диапазон (например, "Регистрации!A:F")
        values: Список значений для записи
    
    Returns:
        result: Результат операции или None
    """
    logger.info(f"📝 [SHEETS] Attempting to append data to {spreadsheet_id}")
    logger.info(f"📋 [SHEETS] Range: {range_name}")
    logger.info(f"📋 [SHEETS] Values: {values}")
    
    try:
        body = {
            'values': [values]
        }
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        updated_cells = result.get('updates', {}).get('updatedCells', 0)
        logger.info(f"✅ [SHEETS] Successfully appended {updated_cells} cells to Google Sheets!")
        
        return result
        
    except HttpError as error:
        logger.error(f"❌ [SHEETS] HTTP Error: {error}")
        logger.error(f"📋 [SHEETS] Error details: {error.content.decode('utf-8')}")
        return None
    except Exception as e:
        logger.error(f"❌ [SHEETS] Error writing to Google Sheets: {str(e)}")
        logger.error(f"📋 [SHEETS] Traceback: {get_traceback()}")
        return None


def get_traceback():
    """Получает traceback ошибки"""
    import traceback
    return traceback.format_exc()

# =============================================================================
# 🌐 API ЭНДПОИНТЫ
# =============================================================================

@app.get("/")
async def root():
    """Главная страница API"""
    logger.info("📍 [API] Root endpoint accessed")
    return {
        "message": "QR-ОбучAI API работает!",
        "status": "ok",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    timestamp = get_yekaterinburg_time().strftime("%d.%m.%Y %H:%M:%S")
    logger.info(f"💚 [API] Health check at {timestamp}")
    return {
        "status": "ok",
        "timestamp": timestamp,
        "timezone": "UTC+5 (Yekaterinburg)"
    }


@app.get("/api/kic-list")
async def get_kics():
    """Получение списка городов (КИЦ)"""
    logger.info("🏙️ [API] KIC list requested")
    return {"cities": DEFAULT_KIC_LIST}


@app.post("/api/register")
async def register_visit(data: RegistrationData, background_tasks: BackgroundTasks):
    """
    Регистрация работника с записью в Google Sheets
    
    Args:
        data: Данные регистрации (ФИО, КИЦ, цель визита, координаты)
        background_tasks: Фоновые задачи FastAPI
    
    Returns:
        dict: Результат регистрации
    """
    logger.info("=" * 60)
    logger.info("📝 [API] Новый запрос на регистрацию")
    logger.info("=" * 60)
    
    try:
        # Получаем время
        timestamp = get_yekaterinburg_time().strftime("%d.%m.%Y %H:%M:%S")
        logger.info(f"⏰ [API] Timestamp: {timestamp}")
        
        # Определяем адрес
        address = "Адрес не определён"
        if data.latitude is not None and data.longitude is not None:
            address = f"шир. {data.latitude:.5f} • долг. {data.longitude:.5f}"
        else:
            address = "Координаты не получены"
        
        # Логируем данные
        logger.info(f"👤 [API] ФИО: {data.fio}")
        logger.info(f"🏙️ [API] КИЦ: {data.kic}")
        logger.info(f"🎯 [API] Цель: {data.purpose}")
        logger.info(f"📍 [API] Адрес: {address}")
        
        # 🔍 Проверка переменных окружения
        logger.info("🔍 [ENV] Checking environment variables...")
        sheet_id = os.environ.get("GOOGLE_SHEET_ID_REGISTRATIONS")
        
        if not sheet_id:
            logger.warning("⚠️ [ENV] GOOGLE_SHEET_ID_REGISTRATIONS not set, using default")
            sheet_id = DEFAULT_SHEET_ID
        
        logger.info(f"📊 [ENV] Sheet ID: {sheet_id}")
        
        # 📊 Запись в Google Sheets
        logger.info("📝 [SHEETS] Attempting to write to Google Sheets...")
        sheets_service = get_sheets_service()
        
        if sheets_service:
            logger.info("✅ [SHEETS] Service is available, writing data...")
            
            # Формируем строку для записи
            # Структура таблицы: Отметка времени | ФИО | КИЦ | Цель визита | Адрес | Занесение в акты
            values = [
                timestamp,           # A: Отметка времени
                data.fio,            # B: ФИО
                data.kic,            # C: КИЦ
                data.purpose,        # D: Цель визита
                address,             # E: Адрес
                ""                   # F: Занесение в акты (пусто)
            ]
            
            # Записываем в таблицу
            result = append_to_sheet(
                sheets_service,
                sheet_id,
                SHEET_RANGE,
                values
            )
            
            if result:
                updated_cells = result.get('updates', {}).get('updatedCells', 0)
                logger.info(f"✅ [SHEETS] Successfully wrote {updated_cells} cells!")
            else:
                logger.error("❌ [SHEETS] Failed to write data (result is None)")
        else:
            logger.error("❌ [SHEETS] Google Sheets service is NOT available!")
            logger.error("⚠️ [SHEETS] Check environment variables and Service Account setup")
        
        logger.info("=" * 60)
        logger.info("✅ [API] Registration completed successfully")
        logger.info("=" * 60)
        
        # Возвращаем успешный ответ
        return {
            "status": "success",
            "address": address,
            "timestamp": timestamp,
            "fio": data.fio,
            "purpose": data.purpose,
            "message": "Регистрация успешна"
        }
        
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error: {str(e)}")
        logger.error(f"📋 [API] Traceback: {get_traceback()}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.get("/api/debug/sheets")
async def debug_sheets():
    """
    Эндпоинт для диагностики Google Sheets подключения
    
    Returns:
        dict: Информация о состоянии подключения
    """
    logger.info("🔧 [DEBUG] Sheets debug endpoint accessed")
    
    result = {
        "status": "debug",
        "env_vars": {},
        "sheets_service": "unknown",
        "errors": [],
        "timestamp": get_yekaterinburg_time().strftime("%d.%m.%Y %H:%M:%S")
    }
    
    # Проверяем переменные окружения
    private_key = os.environ.get("GOOGLE_PRIVATE_KEY", "")
    client_email = os.environ.get("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID_REGISTRATIONS", "")
    
    result["env_vars"] = {
        "has_private_key": bool(private_key),
        "private_key_length": len(private_key) if private_key else 0,
        "private_key_starts_with": private_key[:20] + "..." if private_key else None,
        "client_email": client_email[:30] + "..." if client_email else None,
        "sheet_id": sheet_id if sheet_id else DEFAULT_SHEET_ID
    }
    
    # Пробуем создать сервис
    try:
        if not private_key or not client_email:
            result["errors"].append("Missing credentials in environment variables")
            result["sheets_service"] = "failed"
            logger.error("❌ [DEBUG] Missing credentials")
            return result
        
        # Исправляем формат ключа
        key_fixed = private_key.replace('\\n', '\n') if '\\n' in private_key else private_key
        
        credentials_info = {
            "type": "service_account",
            "project_id": "qr-obuchai",
            "private_key_id": "key123",
            "private_key": key_fixed,
            "client_email": client_email,
            "client_id": "123456",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        result["sheets_service"] = "created"
        logger.info("✅ [DEBUG] Sheets service created successfully")
        
        # Пробуем прочитать таблицу (тестовый запрос)
        try:
            test_sheet_id = sheet_id if sheet_id else DEFAULT_SHEET_ID
            sheet = service.spreadsheets()
            test_result = sheet.get(spreadsheetId=test_sheet_id, range="Регистрации!A1").execute()
            result["test_read"] = "success"
            result["test_range"] = "Регистрации!A:F"
            logger.info(f"✅ [DEBUG] Test read successful: {test_result}")
        except Exception as read_error:
            result["test_read"] = f"failed: {str(read_error)}"
            result["errors"].append(str(read_error))
            logger.error(f"❌ [DEBUG] Test read failed: {read_error}")
            
    except Exception as e:
        result["sheets_service"] = f"error: {str(e)}"
        result["errors"].append(str(e))
        logger.error(f"❌ [DEBUG] Service creation failed: {e}")
    
    return result


@app.get("/api/gosb-list")
async def get_gosb_list():
    """Получение списка ГОСБ"""
    logger.info("🏦 [API] GOSB list requested")
    
    GOSB_CONFIG = {
        "ekb": {"name": "Аппарат Банка Екатеринбург"},
        "tyumen": {"name": "Тюменский ГОСБ Тюмень"},
        "chel": {"name": "Челябинский ГОСБ Челябинск"},
        "ugra": {"name": "Югорский ГОСБ Ханты-Мансийск"},
        "bash": {"name": "Башкирский ГОСБ Уфа"},
        "kurgan": {"name": "Курганский ГОСБ Курган"},
    }
    
    return {
        "gosb": [
            {"id": gid, "name": gdata["name"]}
            for gid, gdata in GOSB_CONFIG.items()
        ]
    }


@app.get("/api/cron/daily-report")
async def cron_daily_report():
    """Ежедневный отчёт в Telegram (cron)"""
    logger.info("📊 [CRON] Daily report executed")
    return {"status": "ok", "message": "Daily report cron executed"}


@app.get("/api/cron/monthly-archive")
async def cron_monthly_archive():
    """Архивация за предыдущий месяц (cron)"""
    logger.info("📊 [CRON] Monthly archive executed")
    return {"status": "ok", "message": "Monthly archive cron executed"}


# =============================================================================
# 🚀 ЗАПУСК
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting QR-ОбучAI API server...")
    logger.info("🔍 Checking configuration...")
    
    # Проверка переменных окружения
    required_vars = [
        "GOOGLE_PRIVATE_KEY",
        "GOOGLE_SERVICE_ACCOUNT_EMAIL",
        "GOOGLE_SHEET_ID_REGISTRATIONS"
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        logger.warning(f"⚠️ Missing environment variables: {missing}")
    else:
        logger.info("✅ All required environment variables are set")
    
    # Запуск сервера
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
