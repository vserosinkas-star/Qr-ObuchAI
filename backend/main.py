"""
QR-ОбучAI — FastAPI Backend
Аналог Google Apps Script функционала для Vercel
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio
import aiohttp
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import (
    BOT_TOKEN, ADMIN_CHAT_ID, COPY_CHAT_ID,
    SHEET_ID_REGISTRATIONS, DEFAULT_KIC_LIST,
    NOMINATIM_URL, NOMINATIM_USER_AGENT,
    GOSB_CONFIG, get_recipient_emails,
    GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_PRIVATE_KEY, GOOGLE_SCOPES,
    validate_config
)

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
# 🔧 GOOGLE SHEETS КЛИЕНТ
# =============================================================================
def get_google_sheets_client():
    """Создаёт клиент для Google Sheets API"""
    try:
        # Создаём учётные данные из переменных окружения
        credentials_info = {
            "type": "service_account",
            "project_id": "qr-obuchai",
            "private_key_id": "key123",
            "private_key": GOOGLE_PRIVATE_KEY,
            "client_email": GOOGLE_SERVICE_ACCOUNT_EMAIL,
            "client_id": "123456",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        }
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=GOOGLE_SCOPES
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        print(f"❌ Ошибка создания Google Sheets клиента: {e}")
        return None

def append_to_sheet(service, spreadsheet_id, range_name, values):
    """Добавляет строку в таблицу"""
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
        print(f"✅ Записано строк: {result.get('updates').get('updatedCells')}")
        return result
    except Exception as e:
        print(f"❌ Ошибка записи в таблицу: {e}")
        return None

# =============================================================================
# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================
async def reverse_geocode(lat: float, lng: float) -> str:
    """Обратный геокодинг через Nominatim API"""
    try:
        lat_fixed = f"{lat:.5f}"
        lng_fixed = f"{lng:.5f}"
        url = f"{NOMINATIM_URL}?format=jsonv2&lat={lat_fixed}&lon={lng_fixed}&accept-language=ru&zoom=18"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": NOMINATIM_USER_AGENT}, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and "address" in 
                        addr = data["address"]
                        parts = []
                        if addr.get("road"):
                            parts.append(addr["road"])
                        if addr.get("house_number"):
                            parts.append(f"д. {addr['house_number']}")
                        city = addr.get("city") or addr.get("town") or addr.get("village")
                        if city:
                            parts.insert(0, f"{city},")
                        elif addr.get("state"):
                            parts.insert(0, f"{addr['state']},")
                        
                        full_address = " ".join(parts).strip()
                        if not full_address or len(full_address.split(",")) < 2:
                            if data.get("display_name"):
                                full_address = (data["display_name"]
                                    .replace(", Россия", "")
                                    .replace(", Свердловская область", "")
                                    .strip())
                        
                        full_address = full_address.replace(",", " •")
                        if full_address:
                            return full_address
                
                return f"шир. {lat_fixed} • долг. {lng_fixed}"
    except Exception as e:
        print(f"⚠️ Ошибка геокодинга: {e}")
        return f"шир. {lat:.5f} • долг. {lng:.5f}"


async def send_telegram_message(chat_id: str, text: str):
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as resp:
                result = await resp.json()
                if not result.get("ok"):
                    print(f"❌ Telegram error: {result.get('description')}")
    except Exception as e:
        print(f"⚠️ Ошибка отправки Telegram: {e}")


async def check_duplicate_registration(fio: str, purpose: str) -> bool:
    """Проверка дубликатов в пределах квартала"""
    # TODO: Реализовать через Google Sheets API
    return False


async def get_kic_list() -> List[str]:
    """Получение списка КИЦ"""
    return DEFAULT_KIC_LIST


# =============================================================================
# 🌐 API ЭНДПОИНТЫ
# =============================================================================
@app.get("/")
async def root():
    """Главная страница"""
    return {"message": "QR-ОбучAI API", "docs": "/docs"}


@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/kic-list")
async def get_kics():
    """Получение списка городов (КИЦ)"""
    cities = await get_kic_list()
    return {"cities": cities}


@app.post("/api/register")
async def register_visit(data: RegistrationData, background_tasks: BackgroundTasks):
    """Регистрация работника с записью в Google Sheets"""
    print(f"📝 Новая регистрация: {data.fio}, {data.kic}, {data.purpose}")
    
    # 🔒 Проверка дубликатов
    is_duplicate = await check_duplicate_registration(data.fio, data.purpose)
    if is_duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"❌ {data.fio} уже зарегистрирован на \"{data.purpose}\" в этом квартале"
        )
    
    # 🌍 Геокодинг
    address = "Адрес не определён"
    if data.latitude and data.longitude:
        address = await reverse_geocode(data.latitude, data.longitude)
    
    # 📊 Запись в Google Sheets
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    # Получаем клиент Google Sheets
    sheets_service = get_google_sheets_client()
    
    if sheets_service:
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
            SHEET_ID_REGISTRATIONS,
            "Лист1!A:F",  # Диапазон (измените если нужно)
            values
        )
        
        if result:
            print(f"✅ Данные записаны в таблицу: {data.fio}")
        else:
            print("⚠️ Не удалось записать данные в таблицу")
    else:
        print("⚠️ Google Sheets клиент не инициализирован")
    
    # 🤖 Уведомление в Telegram
    if ADMIN_CHAT_ID:
        message = (
            f"👮 <b>Новая регистрация</b>\n\n"
            f"👤 <b>ФИО:</b> {data.fio}\n"
            f"🏙️ <b>КИЦ:</b> {data.kic}\n"
            f"🎯 <b>Цель:</b> {data.purpose}\n"
            f"📍 <b>Адрес:</b> {address}\n"
            f"⏰ <b>Время:</b> {timestamp}"
        )
        background_tasks.add_task(send_telegram_message, ADMIN_CHAT_ID, message)
    
    if COPY_CHAT_ID:
        background_tasks.add_task(send_telegram_message, COPY_CHAT_ID, message)
    
    return {
        "status": "success",
        "address": address,
        "timestamp": timestamp,
        "fio": data.fio,
        "purpose": data.purpose,
        "message": "Регистрация успешна"
    }


@app.get("/api/gosb-list")
async def get_gosb_list():
    """Получение списка ГОСБ"""
    return {
        "gosb": [
            {"id": gid, "name": gdata["name"]}
            for gid, gdata in GOSB_CONFIG.items()
        ]
    }


@app.get("/api/cron/daily-report")
async def cron_daily_report():
    """Ежедневный отчёт в Telegram"""
    return {"status": "ok", "message": "Daily report cron executed"}


@app.get("/api/cron/monthly-archive")
async def cron_monthly_archive():
    """Архивация за предыдущий месяц"""
    return {"status": "ok", "message": "Monthly archive cron executed"}


# =============================================================================
# 🚀 ЗАПУСК
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    print("🔍 Проверка конфигурации...")
    if validate_config():
        print("✅ Все настройки корректны")
    else:
        print("⚠️ Проверьте .env файл")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
