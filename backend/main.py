from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import (
    BOT_TOKEN, ADMIN_CHAT_ID,
    GOSB_CONFIG,
    NOMINATIM_URL, NOMINATIM_USER_AGENT,
    get_yekaterinburg_time,
    validate_config
)

app = FastAPI(title="QR-ОбучAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegistrationData(BaseModel):
    fio: str
    kic: str
    purpose: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gosb_id: str = 'ekb'  # По умолчанию Аппарат Банка

def get_sheets_service():
    """Создаёт клиент Google Sheets"""
    try:
        private_key = os.environ.get("GOOGLE_PRIVATE_KEY", "")
        client_email = os.environ.get("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
        
        if not private_key or not client_email:
            print("⚠️ Google credentials not found")
            return None
        
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
        
        credentials_info = {
            "type": "service_account",
            "project_id": "qr-obuchai",
            "private_key_id": "key123",
            "private_key": private_key,
            "client_email": client_email,
            "client_id": "123456",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        print("✅ Google Sheets client created")
        return service
    except Exception as e:
        print(f"❌ Error creating Sheets client: {str(e)}")
        return None

async def reverse_geocode(lat: float, lng: float) -> str:
    import aiohttp
    try:
        lat_fixed = f"{lat:.5f}"
        lng_fixed = f"{lng:.5f}"
        url = f"{NOMINATIM_URL}?format=jsonv2&lat={lat_fixed}&lon={lng_fixed}&accept-language=ru&zoom=18"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": NOMINATIM_USER_AGENT}, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and "address" in data:
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

@app.get("/")
async def root():
    return {"message": "QR-ОбучAI API работает!", "status": "ok"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": get_yekaterinburg_time().strftime("%d.%m.%Y %H:%M:%S")}

@app.get("/api/kic-list")
async def get_kics(gosb: str = 'ekb'):
    """Получение списка КИЦ для конкретного ГОСБ"""
    if gosb in GOSB_CONFIG:
        return {"cities": GOSB_CONFIG[gosb]['cities']}
    return {"cities": GOSB_CONFIG['ekb']['cities']}

@app.post("/api/register")
async def register_visit(data: RegistrationData, background_tasks: BackgroundTasks):
    """Регистрация с записью в таблицу конкретного ГОСБ"""
    timestamp = get_yekaterinburg_time().strftime("%d.%m.%Y %H:%M:%S")
    
    # Определяем ГОСБ
    gosb_id = data.gosb_id if data.gosb_id in GOSB_CONFIG else 'ekb'
    gosb_config = GOSB_CONFIG[gosb_id]
    
    address = "Адрес не определён"
    if data.latitude and data.longitude:
        address = await reverse_geocode(data.latitude, data.longitude)
    
    print(f"📝 Registration: {data.fio}, {gosb_config['name']}, {data.kic}, {data.purpose}")
    
    # Запись в Google Sheets конкретного ГОСБ
    sheets_service = get_sheets_service()
    sheet_id = gosb_config['sheet_id']
    
    if sheets_service and sheet_id:
        try:
            values = [
                timestamp,
                data.fio,
                data.kic,
                data.purpose,
                address,
                ""
            ]
            
            body = {'values': [values]}
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range="Регистрации!A:F",
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✅ Appended {result.get('updates').get('updatedCells')} cells to {gosb_config['name']}")
        except Exception as e:
            print(f"❌ Error writing to Google Sheets: {str(e)}")
    else:
        print(f"⚠️ Google Sheets service not available for {gosb_config['name']}")
    
    return {
        "status": "success",
        "address": address,
        "timestamp": timestamp,
        "fio": data.fio,
        "purpose": data.purpose,
        "gosb": gosb_config['name'],
        "message": "Регистрация успешна"
    }

if __name__ == "__main__":
    import uvicorn
    print("🔍 Checking config...")
    if validate_config():
        print("✅ Config OK")
    uvicorn.run(app, host="0.0.0.0", port=8000)
