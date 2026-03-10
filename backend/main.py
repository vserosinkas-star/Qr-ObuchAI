from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

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

DEFAULT_KIC_LIST = [
    "Екатеринбург", "Нижний Тагил", "Асбест", "Первоуральск",
    "Каменск-Уральский", "Ирбит", "Серов", "Камышлов",
]

def get_yekaterinburg_time():
    return datetime.utcnow() + timedelta(hours=5)

def get_sheets_service():
    """Создаёт клиент Google Sheets с подробным логированием"""
    print("🔍 [SHEETS] Начинаю создание сервиса...")
    
    try:
        private_key = os.environ.get("GOOGLE_PRIVATE_KEY", "")
        client_email = os.environ.get("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
        
        print(f"🔑 [SHEETS] Client email: {client_email[:30]}...")
        print(f"🔑 [SHEETS] Private key length: {len(private_key)}")
        
        if not private_key or not client_email:
            print("❌ [SHEETS] Google credentials not found in environment variables!")
            return None
        
        # Исправляем формат ключа
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
            print("🔧 [SHEETS] Fixed private key format (replaced \\n with newline)")
        
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
        
        print("🔐 [SHEETS] Creating credentials from service account info...")
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        print("🔗 [SHEETS] Building Sheets API client...")
        service = build('sheets', 'v4', credentials=credentials)
        
        print("✅ [SHEETS] Google Sheets client created successfully!")
        return service
    except Exception as e:
        print(f"❌ [SHEETS] Error creating Sheets client: {str(e)}")
        import traceback
        print(f"📋 [SHEETS] Traceback: {traceback.format_exc()}")
        return None

@app.get("/")
async def root():
    return {"message": "QR-ОбучAI API работает!", "status": "ok"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": get_yekaterinburg_time().strftime("%d.%m.%Y %H:%M:%S")}

@app.get("/api/kic-list")
async def get_kics():
    return {"cities": DEFAULT_KIC_LIST}

@app.post("/api/register")
async def register_visit(data: RegistrationData, background_tasks: BackgroundTasks):
    """Регистрация с записью в Google Sheets"""
    print("=" * 60)
    print(" [API] Новый запрос на регистрацию")
    print("=" * 60)
    
    try:
        timestamp = get_yekaterinburg_time().strftime("%d.%m.%Y %H:%M:%S")
        print(f"⏰ [API] Timestamp: {timestamp}")
        
        # Геокодинг
        address = "Адрес не определён"
        if data.latitude is not None and data.longitude is not None:
            address = f"шир. {data.latitude:.5f} • долг. {data.longitude:.5f}"
        else:
            address = "Координаты не получены"
        
        print(f"👤 [API] ФИО: {data.fio}")
        print(f"🏙️ [API] КИЦ: {data.kic}")
        print(f"🎯 [API] Цель: {data.purpose}")
        print(f"📍 [API] Адрес: {address}")
        
        # 🔍 Проверка переменных окружения
        print("🔍 [ENV] Checking environment variables...")
        sheet_id = os.environ.get("GOOGLE_SHEET_ID_REGISTRATIONS")
        print(f"📊 [ENV] Sheet ID: {sheet_id}")
        
        if not sheet_id:
            print("⚠️ [ENV] GOOGLE_SHEET_ID_REGISTRATIONS not set, using default")
            sheet_id = "1BUjdLdJJeGHxnY1ZQ-XD0wbX0HlcZUCffIGF2gG56No"
        
        # Запись в Google Sheets
        print("📝 [SHEETS] Attempting to write to Google Sheets...")
        sheets_service = get_sheets_service()
        
        if sheets_service:
            print("✅ [SHEETS] Service is available, writing data...")
            try:
                values = [
                    timestamp,
                    data.fio,
                    data.kic,
                    data.purpose,
                    address,
                    ""
                ]
                
                print(f"📋 [SHEETS] Values to write: {values}")
                print(f"📄 [SHEETS] Range: Регистрации!A:F")
                
                body = {'values': [values]}
                result = sheets_service.spreadsheets().values().append(
                    spreadsheetId=sheet_id,
                    range="Регистрации!A:F",
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                updated_cells = result.get('updates').get('updatedCells', 0)
                print(f"✅ [SHEETS] Successfully appended {updated_cells} cells to Google Sheets!")
                
            except Exception as e:
                print(f"❌ [SHEETS] Error writing to Google Sheets: {str(e)}")
                import traceback
                print(f"📋 [SHEETS] Traceback: {traceback.format_exc()}")
        else:
            print("❌ [SHEETS] Google Sheets service is NOT available!")
            print("⚠️ [SHEETS] Check environment variables and Service Account setup")
        
        print("=" * 60)
        print("✅ [API] Registration completed successfully")
        print("=" * 60)
        
        return {
            "status": "success",
            "address": address,
            "timestamp": timestamp,
            "fio": data.fio,
            "purpose": data.purpose,
            "message": "Регистрация успешна"
        }
    except Exception as e:
        print(f"❌ [API] Unexpected error: {str(e)}")
        import traceback
        print(f"📋 [API] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting QR-ОбучAI API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
