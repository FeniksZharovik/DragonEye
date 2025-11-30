# backend/main.py

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from pydantic import BaseModel
from typing import Literal

from core.database import engine, get_db
from core.mqtt import init_mqtt, publish_grade, get_mqtt_grade, get_mqtt_weight, GRADE_TOPIC

# Auth & User
from auth.session import get_session
from controllers.UserController import get_user_by_uid

# Services
from services.pcv.pipeline import process_image_bytes
from services.fuzzy.mamdani import compute_fuzzy_score
from services.mqtt_service import publish_command
from services.pcv.normalization import normalize_fixed

# Routers
from routes.grading_routes import router as grading_router
from routes.device_routes import router as device_router
from routes.camera_routes import router as camera_router
from auth.api_login import router as api_auth_router
from routes.metrics_routes import router as metrics_router
from routes.user import router as user_router
from controllers.GradingresultController import router as gradingresult_router

# Request models
class GradeRequest(BaseModel):
    grade: Literal["A", "B", "C"]


app = FastAPI(title="Dragon Fruit Grading API")

# ==========================
# CORS - MUST BE FIRST!
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# ==========================
# MQTT STARTUP
# ==========================
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing MQTT client...")
    init_mqtt()


# ==========================
# MQTT MANUAL CONTROL API
# ==========================
@app.post("/set-grade")
async def set_grade(req: GradeRequest):
    publish_grade(req.grade)
    return {
        "message": f"Grade set to '{req.grade}'",
        "grade": req.grade
    }

@app.get("/current-grade")
async def current_grade():
    current_grade = get_mqtt_grade()
    if current_grade is None:
        raise HTTPException(status_code=400, detail="No grade set. Please use /set-grade to set a grade.")
    return {"current_grade": current_grade}

@app.get("/current-weight")
async def current_weight():
    return {"current_weight": get_mqtt_weight()}

@app.post("/test-send-grade")
async def test_send_grade():
    current_grade = get_mqtt_grade()
    if current_grade is None:
        raise HTTPException(status_code=400, detail="No grade available. Please use /set-grade first.")
    publish_grade(current_grade)
    return {
        "message": f"Current grade '{current_grade}' republished to {GRADE_TOPIC}",
        "grade": current_grade
    }

# ==========================
# Endpoint Upload Gambar
# ==========================
@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    """Process uploaded image with AI/PCV pipeline and fuzzy logic"""
    # Baca file gambar yang diupload
    img_bytes = await file.read()

    # Proses gambar menggunakan pipeline AI/PCV
    try:
        result = process_image_bytes(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proses gambar gagal: {str(e)}")

    # Ambil fitur dari hasil pemrosesan
    length_cm = result['length_cm']
    diameter_cm = result['diameter_cm']
    weight_est_g = result['weight_est_g']
    ratio = result['ratio']

    # Normalisasi fitur untuk fuzzy logic
    length_n = normalize_fixed(length_cm, 0, 100)
    diameter_n = normalize_fixed(diameter_cm, 0, 50)
    weight_n = normalize_fixed(weight_est_g, 0, 1000)
    ratio_n = normalize_fixed(ratio, 0, 2)

    # Hitung skor fuzzy
    fuzzy_score = compute_fuzzy_score(length_n, diameter_n, weight_n, ratio_n)

    # Tentukan grade berdasarkan berat
    grade = grade_from_weight(weight_est_g)

    # Kirim grade dan perintah ke IoT via MQTT
    command = {
        "grade": grade,
        "weight": weight_est_g,
        "score": fuzzy_score
    }
    publish_command(command)

    return {
        "message": "Gambar berhasil diproses",
        "result": {
            "length_cm": length_cm,
            "diameter_cm": diameter_cm,
            "weight_est_g": weight_est_g,
            "ratio": ratio,
            "fuzzy_score": fuzzy_score,
            "grade": grade
        }
    }

# ==========================
# HELPER FUNCTIONS
# ==========================
def grade_from_weight(weight_g: float) -> str:
    """Determine grade based on weight (in grams)"""
    if weight_g >= 350:
        return "A"
    elif weight_g >= 200:
        return "B"
    else:
        return "C"


# ==========================
# ROUTERS
# ==========================
app.include_router(gradingresult_router, prefix="/api/gradingresult", tags=["Grading Results"])
app.include_router(metrics_router, prefix="/api", tags=["Metrics"])
app.include_router(grading_router, prefix="/grading", tags=["Grading"])
app.include_router(camera_router, prefix="/camera", tags=["Camera"])
app.include_router(device_router, prefix="/device", tags=["Device / IoT"])
app.include_router(api_auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["Users"])

# ==========================
# ROOT & HEALTH
# ==========================
@app.get("/")
async def root():
    return {"message": "Dragon Fruit Grading API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).fetchone()[0]
        return {"status": "ok", "database": f"PostgreSQL {version}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/debug/db-status")
async def debug_db_status():
    """Debug endpoint to check database and grading_results table status"""
    try:
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'grading_results'
                )
            """)).fetchone()
            
            table_exists = result[0] if result else False
            
            if table_exists:
                # Count records
                count_result = conn.execute(text("SELECT COUNT(*) FROM grading_results")).fetchone()
                record_count = count_result[0] if count_result else 0
                
                return {
                    "status": "ok",
                    "table_exists": True,
                    "table_name": "grading_results",
                    "record_count": record_count,
                    "message": f"Table exists with {record_count} records"
                }
            else:
                return {
                    "status": "warning",
                    "table_exists": False,
                    "table_name": "grading_results",
                    "message": "Table does not exist. Run migrations or create it."
                }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "message": "Failed to check database status"
        }
    
# ==========================
# DATABASE MIGRATIONS
# ==========================
@app.post("/debug/create-tables")
async def create_tables():
    """Create all database tables from models"""
    try:
        from core.database import Base
        Base.metadata.create_all(bind=engine)
        return {
            "status": "ok",
            "message": "All tables created successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "message": "Failed to create tables"
        }

# ==========================
# DEBUG: List all routes (optional, remove in production)
# ==========================
@app.get("/debug/routes")
def debug_routes():
    routes = [r.path for r in app.routes if hasattr(r, 'path')]
    return {"routes": sorted(routes)}