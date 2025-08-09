import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from services.mqtt_client import mqtt_ingestion

logger = logging.getLogger(__name__)
router = APIRouter()


def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response"""
    return {"success": True, "data": data, "message": message}


def error_response(message: str, errors: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {"success": False, "data": None, "message": message, "errors": errors or []}


@router.get("/devices")
async def get_devices():
    """Get all devices"""
    try:
        # Get real-time device data from MQTT
        devices = mqtt_ingestion.get_devices()
        
        # If no MQTT data yet, return empty list with message
        if not devices:
            return success_response([], "No devices data available yet. MQTT data loading...")
        
        return success_response(devices, f"Retrieved {len(devices)} devices")
        
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return error_response("Failed to fetch devices", [str(e)])


@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    """Get a specific device by ID"""
    try:
        # Mock single device data
        device = {
            "id": device_id,
            "name": f"Device {device_id}",
            "type": "hvac",
            "location": "Building A - Floor 2",
            "status": "online",
            "lastSeen": "2025-08-07T16:25:00Z",
            "power": 8.5,
            "energy": 42.3,
            "voltage": 240.2,
            "current": 18.7,
            "createdAt": "2025-01-15T10:00:00Z",
            "description": "HVAC system monitoring device",
            "firmware": "1.2.3",
            "model": "EnergyMon-Pro",
        }

        return success_response(device, f"Device {device_id} retrieved successfully")
    except Exception as e:
        logger.error(f"Error fetching device {device_id}: {e}")
        return error_response(f"Failed to fetch device {device_id}", [str(e)])


@router.get("/devices/{device_id}/readings")
async def get_device_readings(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    """Get energy readings for a specific device"""
    try:
        # Get real-time readings from MQTT data
        readings = mqtt_ingestion.get_device_readings(device_id, limit)
        
        if not readings:
            return success_response([], f"No readings available for device {device_id}")

        return success_response(
            readings, f"Retrieved {len(readings)} readings for device {device_id}"
        )
    except Exception as e:
        logger.error(f"Error fetching readings for device {device_id}: {e}")
        return error_response(
            f"Failed to fetch readings for device {device_id}", [str(e)]
        )
