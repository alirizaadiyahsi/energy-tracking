"""
Schemas package for data-ingestion service
"""

from .device import (
    DeviceBase,
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse,
    DeviceStats,
)

__all__ = [
    "DeviceBase",
    "DeviceCreate", 
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceListResponse",
    "DeviceStats",
]
