from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
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

def get_sheets_service():
    """Создаёт клиент Google Sheets"""
    try:
        private_key = os.environ.get("GOOGLE_PRIVATE_KEY", "")
        client_email = os.environ.get("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
        
        if not private_key or not client_email:
            print("⚠️ Google credentials not found")
            return None
        
        # Исправляем формат ключа
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

@app.get("/")
async def root():
    return {"message": "QR-ОбучAI API работает!", "status": "ok"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/kic-list")
async def get_kics():
    return {"cities": DEFAULT_KIC_LIST}

@app.post("/api/register")
async def register_visit(data: RegistrationData, background_tasks: BackgroundTasks):
    """Регистрация с записью в Google Sheets"""
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    address = "Адрес не определён"
    if data.latitude and data.longitude:
        address = f"шир. {data.latitude:.5f} • долг. {data.longitude:.5f}"
    
    print(f"📝 Registration: {data.fio}, {data.kic}, {data.purpose}")
    
    # Запись в Google Sheets
    sheets_service = get_sheets_service()
    sheet_id = os.environ.get("SHEET_ID_REGISTRATIONS", "1BUjdLdJJeGHxnY1ZQ-XD0wbX0HlcZUCffIGF2gG56No")
    
    if sheets_service:
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
            
            print(f"✅ Appended {result.get('updates').get('updatedCells')} cells to Google Sheets")
        except Exception as e:
            print(f"❌ Error writing to Google Sheets: {str(e)}")
    else:
        print("⚠️ Google Sheets service not available")
    
    return {
        "status": "success",
        "address": address,
        "timestamp": timestamp,
        "fio": data.fio,
        "purpose": data.purpose,
        "message": "Регистрация успешна"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
