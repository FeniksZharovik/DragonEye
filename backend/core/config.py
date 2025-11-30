# config

import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "DragonEye Backend"

    # Database
    DATABASE_URL: str | None = None

    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    # CSV Path
    FEATURES_CSV: str | None = None

    # MQTT
    MQTT_BROKER: str
    MQTT_PORT: int
    MQTT_USER: str | None = None
    MQTT_PASS: str | None = None
    MQTT_TOPIC: str | None = None
    MQTT_TLS: int | None = None
    MQTT_TOPIC_WEIGHT: str | None = None
    MQTT_TOPIC_GRADE: str | None = None

    # Directories and image settings
    UPLOAD_DIR: str = "/data/uploads"
    PIXEL_PER_CM_DEFAULT: float = 102.0

    # DB Pool optional settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True   # PENTING: .env kamu memakai UPPERCASE


# WAJIB: Instance Settings untuk di-import oleh modul lain
settings = Settings()