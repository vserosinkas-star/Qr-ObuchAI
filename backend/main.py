"""
QR-ОбучAI — FastAPI Backend
С записью в Google Sheets
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio
import aiohttp
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import (
    BOT_TOKEN, ADMIN_CHAT_ID,
    DEFAULT_KIC_LIST,
    NOMINATIM_URL, NOMINATIM_USER_AGENT,
    SHEET_ID_REGISTRATIONS,
    GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_PRIVATE_KEY, GOOGLE_SCOPES,
    validate_config
)

# =============================================================================
# 🚀 ПРИЛОЖЕНИЕ
# =============================================================================
app = FastAPI(title="QR-ОбучAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 📊 МОДЕЛИ
# =============================================================================
class RegistrationData(BaseModel):
    fio: str
    kic: str
    purpose: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# =============================================================================
# 🔧 GOOGLE SHEETS
# =============================================================================
def get_sheets_service():
    """Создаёт клиент Google Sheets"""
    try:
        if not GOOGLE_PRIVATE_KEY or not GOOGLE_SERVICE_ACCOUNT_EMAIL:
            print("⚠️ Google credentials not configured")
            return None
            
        # Исправляем формат ключа
        private_key = GOOGLE_PRIVATE_KEY
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
        
        credentials_info = {
            "type": "service_account",
            "project_id": "qr-obuchai",
            "private_key_id": "key123",
            "private_key": private_key,
            "client_email": GOOGLE_SERVICE_ACCOUNT_EMAIL,
            "client_id": "123456",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=GOOGLE_SCOPES
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        print("✅ Google Sheets client created")
        return service
    except Exception as e:
        print(f"❌ Error creating Sheets client: {e}")
        return None


def append_to_sheet(service, spreadsheet_id, range_name, values):
    """Добавляет строку в таблицу"""
    try:
        body = {'values': [values]}
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        print(f"✅ Appended {result.get('updates').get('updatedCells')} cells")
        return result
    except Exception as e:
        print(f"❌ Error appending to sheet: {e}")
        return None

# =============================================================================
# 🔧 ФУНКЦИИ
# =============================================================================
async def reverse_geocode(lat: float, lng: float) -> str:
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
                        city = addr.get("city") or addr.get("town")
                        if city:
                            parts.insert(0, f"{city},")
                        
                        full_address = " ".join(parts).strip()
                        if not full_address:
                            full_address = data.get("display_name", f"шир. {lat_fixed} • долг. {lng_fixed}")
                        
                        full_address = full_address.replace(",", " •")
                        return full_address
                
                return f"шир. {lat_fixed} • долг. {lng_fixed}"
    except Exception as e:
        print(f"⚠️ Geocode error: {e}")
        return f"шир. {lat:.5f} • долг. {lng:.5f}"


async def send_telegram_message(chat_id: str, text: str):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as resp:
                result = await resp.json()
                if not result.get("ok"):
                    print(f"❌ Telegram: {result.get('description')}")
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

# =============================================================================
# 🌐 API
# =============================================================================
@app.get("/")
async def root():
    return {"message": "QR-ОбучAI API работает!", "docs": "/docs"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/kic-list")
async def get_kics():
    return {"cities": DEFAULT_KIC_LIST}


@app.post("/api/register")
async def register_visit(data: RegistrationData, background_tasks: BackgroundTasks):
    """Регистрация с записью в Google Sheets"""
    print(f"📝 Registration: {data.fio}, {data.kic}, {data.purpose}")
    
    # Геокодинг
    address = "Адрес не определён"
    if data.latitude and data.longitude:
        address = await reverse_geocode(data.latitude, data.longitude)
    
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    # 📊 Запись в Google Sheets
    sheets_service = get_sheets_service()
    
    if sheets_service and SHEET_ID_REGISTRATIONS:
        try:
            # Структура: Отметка времени | ФИО | КИЦ | Цель визита | Адрес | Занесение в акты
            values = [
                timestamp,           # A
                data.fio,            # B
                data.kic,            # C
                data.purpose,        # D
                address,             # E
                ""                   # F
            ]
            
            result = append_to_sheet(
                sheets_service,
                SHEET_ID_REGISTRATIONS,
                "Лист1!A:F",
                values
            )
            
            if result:
                print(f"✅ Data written to sheet: {data.fio}")
            else:
                print("⚠️ Failed to write to sheet")
        except Exception as e:
            print(f"❌ Sheets error: {e}")
    else:
        print("⚠️ Google Sheets not configured")
    
    # Telegram
    if ADMIN_CHAT_ID and BOT_TOKEN:
        message = (
            f"👮 <b>Новая регистрация</b>\n\n"
            f"👤 <b>ФИО:</b> {data.fio}\n"
            f"🏙️ <b>КИЦ:</b> {data.kic}\n"
            f"🎯 <b>Цель:</b> {data.purpose}\n"
            f"📍 <b>Адрес:</b> {address}\n"
            f"⏰ <b>Время:</b> {timestamp}"
        )
        background_tasks.add_task(send_telegram_message, ADMIN_CHAT_ID, message)
    
    return {
        "status": "success",
        "address": address,
        "timestamp": timestamp,
        "fio": data.fio,
        "purpose": data.purpose,
        "message": "Регистрация успешна"
    }


@app.get("/api/cron/daily-report")
async def cron_daily_report():
    return {"status": "ok", "message": "Daily report executed"}


if __name__ == "__main__":
    import uvicorn
    print("🔍 Checking config...")
    if validate_config():
        print("✅ Config OK")
    uvicorn.run(app, host="0.0.0.0", port=8000)
