# camera routes

from fastapi import APIRouter, UploadFile, File
from controllers.camera_controller import process_image_from_file

router = APIRouter(
    prefix="/camera",
    tags=["Camera"]
)

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Endpoint menerima foto dari React (base64 or file upload)
    lalu menjalankan pipeline PCV + fuzzy + MQTT.
    """
    return await process_image_from_file(file)