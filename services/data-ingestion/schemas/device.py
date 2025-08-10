"""
Pydantic schemas for device management in data-ingestion service
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class DeviceBase(BaseModel):
    """Base device schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Device name")
    device_type: str = Field(..., description="Device type (meter, sensor, gateway, controller)")
    location: Optional[str] = Field(None, max_length=255, description="Device location")
    description: Optional[str] = Field(None, description="Device description")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('device_type')
    def validate_device_type(cls, v):
        allowed_types = ['meter', 'sensor', 'gateway', 'controller']
        if v.lower() not in allowed_types:
            raise ValueError(f'Device type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class DeviceCreate(DeviceBase):
    """Schema for creating a new device"""
    mac_address: Optional[str] = Field(None, max_length=17, description="MAC address (format: XX:XX:XX:XX:XX:XX)")
    ip_address: Optional[str] = Field(None, description="IP address")
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Device configuration")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional device metadata")
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        if v is not None:
            import re
            mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
            if not mac_pattern.match(v):
                raise ValueError('MAC address must be in format XX:XX:XX:XX:XX:XX')
        return v


class DeviceUpdate(BaseModel):
    """Schema for updating an existing device"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Device name")
    device_type: Optional[str] = Field(None, description="Device type")
    location: Optional[str] = Field(None, max_length=255, description="Device location")
    description: Optional[str] = Field(None, description="Device description")
    mac_address: Optional[str] = Field(None, max_length=17, description="MAC address (format: XX:XX:XX:XX:XX:XX)")
    ip_address: Optional[str] = Field(None, description="IP address")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Device configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional device metadata")
    status: Optional[str] = Field(None, description="Device status (online, offline, error, maintenance)")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v
    
    @validator('device_type')
    def validate_device_type(cls, v):
        if v is not None:
            allowed_types = ['meter', 'sensor', 'gateway', 'controller']
            if v.lower() not in allowed_types:
                raise ValueError(f'Device type must be one of: {", ".join(allowed_types)}')
            return v.lower()
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['online', 'offline', 'error', 'maintenance']
            if v.lower() not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
            return v.lower()
        return v
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        if v is not None:
            import re
            mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
            if not mac_pattern.match(v):
                raise ValueError('MAC address must be in format XX:XX:XX:XX:XX:XX')
        return v


class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: str = Field(..., description="Device ID")
    status: str = Field(..., description="Device status")
    mac_address: Optional[str] = Field(None, description="MAC address")
    ip_address: Optional[str] = Field(None, description="IP address")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Device configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional device metadata")
    last_seen: Optional[datetime] = Field(None, description="Last time device was seen")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    owner_id: Optional[str] = Field(None, description="Owner user ID")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    
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
