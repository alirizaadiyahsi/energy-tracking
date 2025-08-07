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

@router.get("/dashboard")
async def get_dashboard_analytics():
    """Get dashboard analytics data"""
    try:
        # Mock alerts data
        alerts = [
            {
                "id": "alert-1",
                "type": "warning",
                "message": "High energy consumption detected in Zone A",
                "isRead": False,
                "createdAt": "2025-08-07T12:00:00Z"
            },
            {
                "id": "alert-2", 
                "type": "info",
                "message": "Device maintenance scheduled for tomorrow",
                "isRead": False,
                "createdAt": "2025-08-07T10:30:00Z"
            }
        ]
        
        # Mock recent readings data
        recent_readings = [
            {
                "id": "reading-1",
                "deviceId": "device-001",
                "deviceName": "HVAC System",
                "timestamp": "2025-08-07T15:45:00Z",
                "power": 8.5,
                "energy": 42.3,
                "voltage": 240.2,
                "current": 18.7,
                "location": "Building A - Floor 2"
            },
            {
                "id": "reading-2",
                "deviceId": "device-002", 
                "deviceName": "Lighting System",
                "timestamp": "2025-08-07T15:40:00Z",
                "power": 3.2,
                "energy": 15.8,
                "voltage": 238.9,
                "current": 7.3,
                "location": "Building A - Floor 1"
            },
            {
                "id": "reading-3",
                "deviceId": "device-003",
                "deviceName": "Server Room",
                "timestamp": "2025-08-07T15:35:00Z", 
                "power": 12.1,
                "energy": 68.9,
                "voltage": 241.5,
                "current": 25.4,
                "location": "Building B - Basement"
            }
        ]
        
        dashboard_data = {
            "totalDevices": 12,
            "onlineDevices": 10,
            "totalEnergyToday": 1250.5,
            "totalEnergyMonth": 35420.8,
            "averagePower": 42.1,
            "alerts": alerts,
            "recentReadings": recent_readings
        }
        return success_response(dashboard_data, "Dashboard data retrieved successfully")
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return error_response("Failed to fetch dashboard data", [str(e)])

@router.get("/consumption/trends")
async def get_consumption_trends(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|yearly)$"),
    device_id: Optional[str] = None
):
    """Get energy consumption trends"""
    try:
        # Mock data for now - replace with actual database queries
        trends_data = [
            {"timestamp": "2025-08-01", "value": 45.2, "label": "Aug 1"},
            {"timestamp": "2025-08-02", "value": 48.1, "label": "Aug 2"},
            {"timestamp": "2025-08-03", "value": 41.8, "label": "Aug 3"},
            {"timestamp": "2025-08-04", "value": 44.5, "label": "Aug 4"},
            {"timestamp": "2025-08-05", "value": 46.7, "label": "Aug 5"},
            {"timestamp": "2025-08-06", "value": 43.2, "label": "Aug 6"},
            {"timestamp": "2025-08-07", "value": 47.9, "label": "Aug 7"}
        ]
        
        result = {
            "period": period,
            "device_id": device_id,
            "trends": trends_data
        }
        return success_response(result, f"Consumption trends for {period} period retrieved successfully")
    except Exception as e:
        logger.error(f"Error fetching consumption trends: {e}")
        return error_response("Failed to fetch consumption trends", [str(e)])

@router.get("/efficiency/analysis")
async def get_efficiency_analysis():
    """Get energy efficiency analysis"""
    return {
        "overall_efficiency": 82.5,
        "device_efficiency": [
            {"device_id": "device-001", "efficiency": 85.2},
            {"device_id": "device-002", "efficiency": 79.8}
        ],
        "improvement_suggestions": [
            "Optimize device-002 operating hours",
            "Consider upgrading old equipment"
        ]
    }

@router.get("/reports/energy")
async def generate_energy_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    device_ids: Optional[List[str]] = Query(None)
):
    """Generate energy consumption report"""
    return {
        "report_id": "RPT-2024-001",
        "period": f"{start_date} to {end_date}",
        "devices": device_ids or ["all"],
        "total_consumption": 2847.6,
        "total_cost": 426.45,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/forecasting")
async def get_consumption_forecast(
    days_ahead: int = Query(30, ge=1, le=365)
):
    """Get energy consumption forecast"""
    return {
        "forecast_period": f"Next {days_ahead} days",
        "predicted_consumption": 1450.8,
        "confidence_interval": {"lower": 1380.2, "upper": 1521.4},
        "forecast_accuracy": 94.2
    }
