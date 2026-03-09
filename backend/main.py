from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

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
    """Простая регистрация без Google Sheets"""
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    address = "Адрес определён"
    if data.latitude and data.longitude:
        address = f"шир. {data.latitude:.5f} • долг. {data.longitude:.5f}"
    
    print(f"✅ Registration: {data.fio}, {data.kic}, {data.purpose}")
    
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
