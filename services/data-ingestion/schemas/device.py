"""
Pydantic schemas for device management in data-ingestion service
"""

from datetime import datetime
from typing import Optional, Dict, Any, Union
import uuid
from pydantic import BaseModel, Field, field_validator


class DeviceBase(BaseModel):
    """Base device schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Device name")
    type: str = Field(..., description="Device type (hvac, lighting, server, etc.)")
    location: Optional[str] = Field(None, max_length=255, description="Device location")
    description: Optional[str] = Field(None, max_length=1000, description="Device description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ['hvac', 'lighting', 'server', 'sensor', 'meter', 'gateway', 'appliance', 'industrial', 'controller']
        if v.lower() not in allowed_types:
            raise ValueError(f'Device type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class DeviceCreate(DeviceBase):
    """Schema for creating a new device"""
    base_power: Optional[float] = Field(None, ge=0.1, le=1000.0, description="Base power consumption in kW")
    base_voltage: Optional[float] = Field(None, ge=100.0, le=600.0, description="Base voltage in V")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")
    model: Optional[str] = Field(None, max_length=100, description="Device model")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional device metadata")


class DeviceUpdate(BaseModel):
    """Schema for updating an existing device"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Device name")
    type: Optional[str] = Field(None, description="Device type")
    location: Optional[str] = Field(None, max_length=255, description="Device location")
    description: Optional[str] = Field(None, max_length=1000, description="Device description")
    base_power: Optional[float] = Field(None, ge=0.1, le=1000.0, description="Base power consumption in kW")
    base_voltage: Optional[float] = Field(None, ge=100.0, le=600.0, description="Base voltage in V")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")
    model: Optional[str] = Field(None, max_length=100, description="Device model")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional device metadata")
    status: Optional[str] = Field(None, description="Device status (online, offline, error)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v is not None:
            allowed_types = ['hvac', 'lighting', 'server', 'sensor', 'meter', 'gateway', 'appliance', 'industrial', 'controller']
            if v.lower() not in allowed_types:
                raise ValueError(f'Device type must be one of: {", ".join(allowed_types)}')
            return v.lower()
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['online', 'offline', 'error', 'maintenance']
            if v.lower() not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
            return v.lower()
        return v


class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: str = Field(..., description="Device ID")
    status: str = Field(..., description="Device status")
    base_power: Optional[float] = Field(None, description="Base power consumption in kW")
    base_voltage: Optional[float] = Field(None, description="Base voltage in V")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    model: Optional[str] = Field(None, description="Device model")
    last_seen: Optional[datetime] = Field(None, description="Last time device was seen")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional device metadata")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Schema for device list response"""
    devices: list[DeviceResponse]
    total: int
    page: int = 1
    limit: int = 100
    
    class Config:
        from_attributes = True


class DeviceStats(BaseModel):
    """Schema for device statistics"""
    total_devices: int
    online_devices: int
    offline_devices: int
    error_devices: int
    device_types: Dict[str, int]
    
    class Config:
        from_attributes = True
