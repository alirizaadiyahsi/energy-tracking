"""
Configuration settings for IoT Mock Service
"""

import os
from typing import List, Union

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = {"extra": "ignore"}  # Ignore extra environment variables
    
    # Service Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8090
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # CORS Origins - accept as string, will be parsed later
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost:8080"
    
    # MQTT Configuration
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "iot_user"
    MQTT_PASSWORD: str = "iot123"
    MQTT_CLIENT_ID_PREFIX: str = "mock_device"
    
    # Device Simulation Configuration
    DEFAULT_DEVICE_COUNT: int = 5
    SIMULATION_INTERVAL: float = 5.0  # seconds between data sends
    DATA_VARIATION_PERCENT: float = 0.1  # 10% variation in readings
    
    # Anomaly Generation Configuration
    ANOMALY_CHANCE: float = 0.02  # 2% chance of anomaly per reading
    ANOMALY_POWER_MULTIPLIER_MIN: float = 2.0  # Minimum power multiplier for anomalies
    ANOMALY_POWER_MULTIPLIER_MAX: float = 5.0  # Maximum power multiplier for anomalies
    ANOMALY_VOLTAGE_VARIATION: float = 0.2  # ±20% voltage variation during anomalies
    ANOMALY_DURATION_MIN: int = 3  # Minimum readings for sustained anomaly
    ANOMALY_DURATION_MAX: int = 10  # Maximum readings for sustained anomaly
    
    # Energy Data Ranges
    POWER_MIN: float = 0.5  # kW
    POWER_MAX: float = 50.0  # kW
    VOLTAGE_NOMINAL: float = 240.0  # V
    VOLTAGE_TOLERANCE: float = 5.0  # V
    
    # Device Types Configuration
    DEVICE_TYPES: List[str] = [
        "hvac",
        "lighting", 
        "server",
        "industrial",
        "appliance"
    ]
    
    # MQTT Topics
    MQTT_TOPIC_PREFIX: str = "energy/devices"
    DATA_TOPIC_SUFFIX: str = "data"
    STATUS_TOPIC_SUFFIX: str = "status"
    COMMAND_TOPIC_SUFFIX: str = "commands"
    
    @field_validator("DEVICE_TYPES", mode="before")
    @classmethod
    def parse_device_types(cls, v):
        """Parse device types from string or list"""
        if isinstance(v, str):
            return [device_type.strip() for device_type in v.split(",")]
        elif isinstance(v, list):
            return v
        return [str(v)]
    
    def get_data_topic(self, device_id: str) -> str:
        """Get MQTT data topic for device"""
        return f"{self.MQTT_TOPIC_PREFIX}/{device_id}/{self.DATA_TOPIC_SUFFIX}"
    
    def get_status_topic(self, device_id: str) -> str:
        """Get MQTT status topic for device"""
        return f"{self.MQTT_TOPIC_PREFIX}/{device_id}/{self.STATUS_TOPIC_SUFFIX}"
    
    def get_command_topic(self, device_id: str) -> str:
        """Get MQTT command topic for device"""
        return f"{self.MQTT_TOPIC_PREFIX}/{device_id}/{self.COMMAND_TOPIC_SUFFIX}"
    
    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Create global settings instance
settings = Settings()
