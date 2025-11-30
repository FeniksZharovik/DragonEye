# routes/device_routes.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from services import mqtt_service
from models.grading_model import GradingResult
from core.database import get_db

router = APIRouter()

# -----------------------------
# Pydantic Model untuk ESP8266
# -----------------------------
class DevicePayload(BaseModel):
    weight: float
    grade: str = Field(pattern="^(A|B|C)$")   # Validasi Pydantic v2


# -----------------------------
# STATUS DEVICE
# -----------------------------
@router.get("/device-status")
def device_status():
    return {
        "status": "OK",
        "device": "Sorter_01",
        "uptime": 3600
    }


# -----------------------------
# RECEIVE DATA FROM ESP8266
# -----------------------------
@router.post("/receive")
def receive_data(payload: DevicePayload, db_session: Session = Depends(get_db)):
    print("📩 Data diterima dari ESP8266:", payload)

    # Ambil record terakhir yang belum punya weight_actual & grade
    last_record = (
        db_session.query(GradingResult)
        .filter(
            GradingResult.weight_actual_g.is_(None),
            GradingResult.final_grade.is_(None)
        )
        .order_by(GradingResult.created_at.desc())
        .first()
    )

    if not last_record:
        raise HTTPException(
            status_code=400,
            detail="No matching record found for update."
        )

    # Update record
    last_record.weight_actual_g = payload.weight
    last_record.final_grade = payload.grade
    db_session.commit()

    return {
        "message": "Data received and processed successfully",
        "received": payload
    }


# -----------------------------
# SEND COMMAND TO DEVICE
# -----------------------------
@router.post("/send-command")
def send_command_to_device(command: dict):
    print(f"📤 Perintah dikirim ke perangkat: {command}")
    mqtt_service.publish_command(command)
    return {
        "message": "Command sent to device successfully",
        "command": command
    }