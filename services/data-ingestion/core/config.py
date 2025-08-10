"""
Configuration settings for Data Ingestion Service
"""

import os
from typing import List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Energy Data Ingestion Service"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/energy_tracking"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/2"

    # InfluxDB Settings
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "energy-token"
    INFLUXDB_ORG: str = "energy-org"
    
    # Authentication Service Settings
    AUTH_SERVICE_URL: str = "http://energy-auth-service:8005"
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    
    # Security Settings
    ENABLE_AUTH: bool = True
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    INFLUXDB_BUCKET: str = "iot-data"

    # MQTT Settings
    MQTT_BROKER: str = "mosquitto"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: str = "iot_user"
    MQTT_PASSWORD: str = "iot123"
    MQTT_KEEPALIVE: int = 60
    MQTT_TOPICS: List[str] = [
        "energy/devices/+/data",
        "energy/devices/+/status",
        "energy/devices/+/alerts",
    ]

    # Auth Service
    AUTH_SERVICE_URL: str = "http://localhost:8005"

    # Processing Settings
    BATCH_SIZE: int = 100
    BATCH_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3
    PROCESSING_TIMEOUT: int = 300

    # Data Validation
    MAX_DATA_POINTS_PER_BATCH: int = 1000
    DATA_RETENTION_DAYS: int = 365

    @validator("MQTT_TOPICS", pre=True)
    def parse_mqtt_topics(cls, v):
        if isinstance(v, str):
            return [topic.strip() for topic in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
