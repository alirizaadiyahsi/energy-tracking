"""
Configuration settings for the Authentication Service
"""

import os
from typing import List, Optional

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Energy Tracking Auth Service"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/energy_tracking"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Remember Me Settings
    JWT_REMEMBER_ME_ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    JWT_REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    SESSION_REMEMBER_ME_EXPIRE_DAYS: int = 30

    # Security Settings
    BCRYPT_ROUNDS: int = 12
    SESSION_EXPIRE_HOURS: int = 24
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    # Email Settings
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 2
    EMAIL_FROM: str = "noreply@energytracking.com"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
    ]

    # API Settings
    API_PREFIX: str = "/api/v1"
    RATE_LIMIT_PER_MINUTE: int = 100

    # Service Discovery
    USER_SERVICE_URL: Optional[str] = None
    DATA_SERVICE_URL: Optional[str] = None
    NOTIFICATION_SERVICE_URL: Optional[str] = None

    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("JWT_SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
