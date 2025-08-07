from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response"""
    return {
        "success": True,
        "data": data,
        "message": message
    }

def error_response(message: str, errors: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors or []
    }

@router.get("/devices")
async def get_devices():
    """Get all devices"""
    try:
        # Mock device data for now
        devices = [
            {
                "id": "device-001",
                "name": "HVAC System",
                "type": "hvac",
                "location": "Building A - Floor 2",
                "status": "online",
                "lastSeen": "2025-08-07T16:25:00Z",
                "power": 8.5,
                "energy": 42.3,
                "voltage": 240.2,
                "current": 18.7,
                "createdAt": "2025-01-15T10:00:00Z"
            },
            {
                "id": "device-002", 
                "name": "Lighting System",
                "type": "lighting",
                "location": "Building A - Floor 1",
                "status": "online",
                "lastSeen": "2025-08-07T16:20:00Z",
                "power": 3.2,
                "energy": 15.8,
                "voltage": 238.9,
                "current": 7.3,
                "createdAt": "2025-01-20T14:30:00Z"
            },
            {
                "id": "device-003",
                "name": "Server Room",
                "type": "server",
                "location": "Building B - Basement", 
                "status": "online",
                "lastSeen": "2025-08-07T16:22:00Z",
                "power": 12.1,
                "energy": 68.9,
                "voltage": 241.5,
                "current": 25.4,
                "createdAt": "2025-01-10T09:15:00Z"
            },
            {
                "id": "device-004",
                "name": "Production Line",
                "type": "industrial",
                "location": "Factory - Zone A",
                "status": "offline",
                "lastSeen": "2025-08-07T15:45:00Z",
                "power": 0.0,
                "energy": 0.0,
                "voltage": 0.0,
                "current": 0.0,
                "createdAt": "2025-02-01T08:00:00Z"
            },
            {
                "id": "device-005",
                "name": "Warehouse Lighting",
                "type": "lighting",
                "location": "Warehouse - Section C",
                "status": "error",
                "lastSeen": "2025-08-07T16:15:00Z",
                "power": 2.1,
                "energy": 8.5,
                "voltage": 235.0,
                "current": 4.2,
                "createdAt": "2025-01-25T11:45:00Z"
            }
        ]
        
        return success_response(devices, "Devices retrieved successfully")
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
            "model": "EnergyMon-Pro"
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
    to_date: Optional[str] = Query(None, alias="to")
):
    """Get energy readings for a specific device"""
    try:
        # Mock readings data
        readings = []
        base_time = datetime.now()
        
        for i in range(min(limit, 10)):  # Generate up to 10 sample readings
            reading_time = base_time - timedelta(minutes=i * 5)
            readings.append({
                "id": f"reading-{device_id}-{i}",
                "deviceId": device_id,
                "timestamp": reading_time.isoformat() + "Z",
                "power": 8.5 + (i * 0.2),
                "energy": 42.3 + (i * 2.1),
                "voltage": 240.2 - (i * 0.1),
                "current": 18.7 + (i * 0.3)
            })
        
        return success_response(readings, f"Readings for device {device_id} retrieved successfully")
    except Exception as e:
        logger.error(f"Error fetching readings for device {device_id}: {e}")
        return error_response(f"Failed to fetch readings for device {device_id}", [str(e)])
