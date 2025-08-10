import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from services.device_service import DeviceService
from core.database import get_db
from services.mqtt_client import mqtt_ingestion

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize device service
device_service = DeviceService()


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


# ============================================================================
# DEVICE CRUD ENDPOINTS
# ============================================================================

@router.get("/devices/list", response_model=Dict[str, Any])
async def list_devices_db(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by device status"),
    db: AsyncSession = Depends(get_db)
):
    """List devices from database"""
    try:
        devices = await device_service.list_devices(
            db=db,
            skip=skip,
            limit=limit,
            device_type=device_type,
            status=status
        )
        
        return success_response(
            data=[device.model_dump() for device in devices],
            message=f"Retrieved {len(devices)} devices from database"
        )
        
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list devices"
        )


@router.get("/devices/{device_id}/db", response_model=Dict[str, Any])
async def get_device_db(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific device by ID from database"""
    try:
        device = await device_service.get_device(db=db, device_id=device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        return success_response(
            data=device.model_dump(),
            message=f"Device {device_id} retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device"
        )


@router.post("/devices", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add authentication dependency here
    # current_user = Depends(get_current_user)
):
    """Create a new device"""
    try:
        device = await device_service.create_device(
            db=db,
            device_data=device_data,
            # created_by=current_user.get("user_id")  # TODO: Add when auth is integrated
        )
        
        return success_response(
            data=device.model_dump(),
            message=f"Device '{device.name}' created successfully"
        )
        
    except ValueError as e:
        logger.warning(f"Validation error creating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device"
        )


@router.put("/devices/{device_id}", response_model=Dict[str, Any])
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add authentication dependency here
    # current_user = Depends(get_current_user)
):
    """Update an existing device"""
    try:
        device = await device_service.update_device(
            db=db,
            device_id=device_id,
            device_data=device_data,
            # updated_by=current_user.get("user_id")  # TODO: Add when auth is integrated
        )
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        return success_response(
            data=device.model_dump(),
            message=f"Device '{device.name}' updated successfully"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error updating device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device"
        )


@router.delete("/devices/{device_id}", response_model=Dict[str, Any])
async def delete_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    # TODO: Add authentication dependency here
    # current_user = Depends(get_current_user)
):
    """Delete a device"""
    try:
        deleted = await device_service.delete_device(db=db, device_id=device_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        return success_response(
            data={"deleted": True},
            message=f"Device {device_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device"
        )


@router.get("/devices/stats", response_model=Dict[str, Any])
async def get_device_stats(db: AsyncSession = Depends(get_db)):
    """Get device statistics"""
    try:
        # This could be implemented in device_service if needed
        devices = await device_service.list_devices(db=db, limit=1000)  # Get all for stats
        
        stats = {
            "total_devices": len(devices),
            "online_devices": len([d for d in devices if d.status == "online"]),
            "offline_devices": len([d for d in devices if d.status == "offline"]),
            "error_devices": len([d for d in devices if d.status == "error"]),
            "device_types": {}
        }
        
        # Count device types
        for device in devices:
            device_type = device.type
            stats["device_types"][device_type] = stats["device_types"].get(device_type, 0) + 1
        
        return success_response(
            data=stats,
            message="Device statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting device stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device statistics"
        )
