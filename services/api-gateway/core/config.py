"""
Configuration settings for the API Gateway
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Energy Tracking API Gateway"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/energy_tracking"
    
    # Redis Settings  
    REDIS_URL: str = "redis://localhost:6379/1"
    
    # InfluxDB Settings
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "energy-token"
    INFLUXDB_ORG: str = "energy-org"
    INFLUXDB_BUCKET: str = "iot-data"
    
    # Auth Service
    AUTH_SERVICE_URL: str = "http://localhost:8005"
    
    # JWT Settings (for token verification)
    SECRET_KEY: str = "your-secret-key"
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080"
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Service URLs
    DATA_INGESTION_URL: str = "http://data-ingestion:8001"
    DATA_PROCESSING_URL: str = "http://data-processing:8002"
    ANALYTICS_URL: str = "http://analytics:8003"
    NOTIFICATION_URL: str = "http://notification:8004"
    
    @validator('CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()
