"""
API Routes for IoT Mock Service

Provides REST endpoints for device management and control
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models
class DeviceCreateRequest(BaseModel):
    """Request model for creating a new device"""
    device_type: str = Field(..., description="Type of device (hvac, lighting, server, etc.)")
    name: str = Field(..., description="Human-readable device name")
    location: str = Field(..., description="Physical location of device")
    base_power: float = Field(10.0, ge=0.1, le=1000.0, description="Base power consumption in kW")
    base_voltage: float = Field(240.0, ge=100.0, le=600.0, description="Base voltage in V")


class DeviceUpdateRequest(BaseModel):
    """Request model for updating device settings"""
    name: Optional[str] = Field(None, description="Updated device name")
    location: Optional[str] = Field(None, description="Updated device location")
    base_power: Optional[float] = Field(None, ge=0.1, le=1000.0, description="Updated base power")
    base_voltage: Optional[float] = Field(None, ge=100.0, le=600.0, description="Updated base voltage")
    enabled: Optional[bool] = Field(None, description="Enable/disable device")
    online: Optional[bool] = Field(None, description="Set device online/offline")


class DeviceCommandRequest(BaseModel):
    """Request model for sending commands to devices"""
    command: str = Field(..., description="Command to send")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Command parameters")


class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    data: Optional[Any] = None
    message: str = "Success"
    errors: Optional[List[str]] = None


def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "errors": None
    }


def error_response(message: str, errors: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors or []
    }


# Global access to services (set by main app)
device_manager = None
device_simulator = None


def set_services(dm, ds):
    """Set global service references"""
    global device_manager, device_simulator
    device_manager = dm
    device_simulator = ds


@router.get("/devices")
async def get_devices():
    """Get all mock devices"""
    try:
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        devices = await device_manager.get_all_devices()
        device_list = [device.get_device_info() for device in devices.values()]
        
        return success_response(
            data=device_list,
            message=f"Retrieved {len(device_list)} devices"
        )
        
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    """Get a specific device by ID"""
    try:
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        device = await device_manager.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        return success_response(
            data=device.get_device_info(),
            message=f"Device {device_id} retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices")
async def create_device(request: DeviceCreateRequest):
    """Create a new mock device"""
    try:
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        # Generate device ID
        import uuid
        device_id = f"mock-{request.device_type}-{uuid.uuid4().hex[:8]}"
        
        # Create device
        device = await device_manager.add_device(
            device_id=device_id,
            device_type=request.device_type,
            name=request.name,
            location=request.location,
            base_power=request.base_power,
            base_voltage=request.base_voltage
        )
        
        return success_response(
            data=device.get_device_info(),
            message=f"Device {device_id} created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/devices/{device_id}")
async def update_device(device_id: str, request: DeviceUpdateRequest):
    """Update a mock device"""
    try:
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        device = await device_manager.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Update device properties
        if request.name is not None:
            device.name = request.name
        if request.location is not None:
            device.location = request.location
        if request.base_power is not None:
            device.base_power = request.base_power
        if request.base_voltage is not None:
            device.base_voltage = request.base_voltage
        if request.enabled is not None:
            device.set_enabled(request.enabled)
        if request.online is not None:
            device.set_online(request.online)
        
        return success_response(
            data=device.get_device_info(),
            message=f"Device {device_id} updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/devices/{device_id}")
async def delete_device(device_id: str):
    """Delete a mock device"""
    try:
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        success = await device_manager.remove_device(device_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        return success_response(
            message=f"Device {device_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}/readings")
async def get_device_readings(device_id: str):
    """Get current readings from a device"""
    try:
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        device = await device_manager.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        readings = device.get_current_readings()
        
        return success_response(
            data=readings,
            message=f"Readings for device {device_id} retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting readings for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/{device_id}/command")
async def send_device_command(device_id: str, request: DeviceCommandRequest):
    """Send a command to a device"""
    try:
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        device = await device_manager.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Handle command locally or via MQTT
        command_data = {
            "command": request.command,
            "parameters": request.parameters or {}
        }
        
        # Process command locally (this will also be sent via MQTT)
        await device_manager._handle_device_command(device_id, command_data)
        
        return success_response(
            message=f"Command '{request.command}' sent to device {device_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending command to device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/{device_id}/simulate")
async def simulate_device_data(device_id: str):
    """Manually trigger data simulation for a device"""
    try:
        if not device_simulator:
            raise HTTPException(status_code=503, detail="Device simulator not available")
        
        success = await device_simulator.simulate_device_once(device_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found or simulation failed")
        
        return success_response(
            message=f"Data simulation triggered for device {device_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simulating device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulation/status")
async def get_simulation_status():
    """Get simulation status"""
    try:
        if not device_simulator or not device_manager:
            raise HTTPException(status_code=503, detail="Services not available")
        
        devices = await device_manager.get_all_devices()
        
        status = {
            "is_running": device_simulator.is_running,
            "total_devices": len(devices),
            "online_devices": sum(1 for d in devices.values() if d.is_online),
            "enabled_devices": sum(1 for d in devices.values() if d.is_enabled),
            "mqtt_connected": device_manager.is_connected,
            "simulation_interval": "5.0 seconds"
        }
        
        return success_response(
            data=status,
            message="Simulation status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting simulation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/start")
async def start_simulation():
    """Start device simulation"""
    try:
        if not device_simulator:
            raise HTTPException(status_code=503, detail="Device simulator not available")
        
        if device_simulator.is_running:
            return success_response(message="Simulation is already running")
        
        await device_simulator.start()
        
        return success_response(message="Device simulation started")
        
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/stop")
async def stop_simulation():
    """Stop device simulation"""
    try:
        if not device_simulator:
            raise HTTPException(status_code=503, detail="Device simulator not available")
        
        if not device_simulator.is_running:
            return success_response(message="Simulation is already stopped")
        
        await device_simulator.stop()
        
        return success_response(message="Device simulation stopped")
        
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/device-types")
async def get_device_types():
    """Get available device types"""
    from core.config import settings
    
    return success_response(
        data=settings.DEVICE_TYPES,
        message="Device types retrieved successfully"
    )


class AnomalyTriggerRequest(BaseModel):
    """Request model for manually triggering anomalies"""
    device_id: Optional[str] = Field(None, description="Specific device ID (if None, random device)")
    anomaly_type: Optional[str] = Field(None, description="Type of anomaly to trigger")
    duration: Optional[int] = Field(None, ge=1, le=50, description="Duration in readings")
    power_multiplier: Optional[float] = Field(None, ge=0.5, le=10.0, description="Power multiplier")


@router.post("/trigger-anomaly")
async def trigger_anomaly(request: AnomalyTriggerRequest):
    """Manually trigger an anomaly for testing purposes"""
    try:
        from main import device_manager
        
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        devices = await device_manager.get_all_devices()
        if not devices:
            raise HTTPException(status_code=404, detail="No devices available")
        
        # Select device
        if request.device_id:
            if request.device_id not in devices:
                raise HTTPException(status_code=404, detail=f"Device {request.device_id} not found")
            device = devices[request.device_id]
        else:
            # Select random device
            import random
            device_id = random.choice(list(devices.keys()))
            device = devices[device_id]
        
        # Set anomaly parameters
        import random
        from core.config import settings
        
        anomaly_types = [
            "high_power_consumption",
            "voltage_fluctuation", 
            "power_spike",
            "sustained_high_load"
        ]
        
        anomaly_type = request.anomaly_type or random.choice(anomaly_types)
        duration = request.duration or random.randint(
            settings.ANOMALY_DURATION_MIN, 
            settings.ANOMALY_DURATION_MAX
        )
        power_multiplier = request.power_multiplier or random.uniform(
            settings.ANOMALY_POWER_MULTIPLIER_MIN,
            settings.ANOMALY_POWER_MULTIPLIER_MAX
        )
        
        # Force start anomaly
        device.anomaly_active = True
        device.anomaly_type = anomaly_type
        device.anomaly_remaining_duration = duration
        device.anomaly_power_multiplier = power_multiplier
        device.anomaly_voltage_multiplier = random.uniform(0.8, 1.2)
        
        logger.warning(f"Manually triggered {anomaly_type} anomaly for device {device.device_id} "
                      f"(duration: {duration} readings, power_mult: {power_multiplier:.2f})")
        
        return success_response(
            data={
                "device_id": device.device_id,
                "device_name": device.name,
                "anomaly_type": anomaly_type,
                "duration": duration,
                "power_multiplier": power_multiplier
            },
            message=f"Anomaly triggered for device {device.device_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomaly-status")
async def get_anomaly_status():
    """Get current anomaly status for all devices"""
    try:
        from main import device_manager
        
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        devices = await device_manager.get_all_devices()
        
        anomaly_status = []
        for device_id, device in devices.items():
            status = {
                "device_id": device_id,
                "device_name": device.name,
                "anomaly_active": device.anomaly_active,
                "anomaly_type": device.anomaly_type,
                "anomaly_remaining_duration": device.anomaly_remaining_duration,
                "current_power": device.current_power,
                "base_power": device.base_power,
                "power_ratio": device.current_power / device.base_power if device.base_power > 0 else 0
            }
            anomaly_status.append(status)
        
        active_anomalies = [s for s in anomaly_status if s["anomaly_active"]]
        
        return success_response(
            data={
                "devices": anomaly_status,
                "total_devices": len(anomaly_status),
                "active_anomalies": len(active_anomalies),
                "anomaly_details": active_anomalies
            },
            message="Anomaly status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting anomaly status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-anomalies")
async def clear_all_anomalies():
    """Clear all active anomalies"""
    try:
        from main import device_manager
        
        if not device_manager:
            raise HTTPException(status_code=503, detail="Device manager not available")
        
        devices = await device_manager.get_all_devices()
        cleared_count = 0
        
        for device in devices.values():
            if device.anomaly_active:
                device._end_anomaly()
                cleared_count += 1
        
        return success_response(
            data={"cleared_anomalies": cleared_count},
            message=f"Cleared {cleared_count} active anomalies"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
