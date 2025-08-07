import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres123@localhost:5432/energy_tracking",
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/3")

    # InfluxDB
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "energy-org")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "iot-data")

    # Auth Service
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8005")

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/4")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/4"
    )

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "your-jwt-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
    ]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Processing settings
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "1000"))
    PROCESSING_INTERVAL: int = int(os.getenv("PROCESSING_INTERVAL", "60"))  # seconds
    ANOMALY_DETECTION_THRESHOLD: float = float(
        os.getenv("ANOMALY_DETECTION_THRESHOLD", "2.0")
    )

    class Config:
        env_file = ".env"


settings = Settings()
