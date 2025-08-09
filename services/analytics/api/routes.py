import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx

from fastapi import APIRouter, HTTPException, Query

# Add InfluxDB service import
from services.influx_service import InfluxService
from services.realtime_anomaly_detector import realtime_detector
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Data ingestion service URL (internal docker network)
DATA_INGESTION_URL = "http://data-ingestion:8001"

# Initialize InfluxDB service
influx_service = InfluxService(
    url=settings.INFLUXDB_URL,
    token=settings.INFLUXDB_TOKEN,
    org=settings.INFLUXDB_ORG,
    bucket=settings.INFLUXDB_BUCKET
)


def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response"""
    return {"success": True, "data": data, "message": message}


def error_response(message: str, errors: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {"success": False, "data": None, "message": message, "errors": errors or []}


@router.get("/dashboard")
async def get_dashboard_analytics():
    """Get dashboard analytics data"""
    try:
        # Fetch real device data from data-ingestion service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{DATA_INGESTION_URL}/api/v1/devices", timeout=5.0)
                devices_data = response.json()
                devices = devices_data.get("data", []) if devices_data.get("success") else []
                logger.info(f"Received {len(devices)} devices from data-ingestion")
                # Debug: log first device data
                if devices:
                    logger.info(f"Sample device data: {devices[0]}")
            except Exception as e:
                logger.warning(f"Failed to fetch devices from data-ingestion: {e}")
                devices = []
        
        # Calculate real metrics from device data
        total_devices = len(devices)
        online_devices = len([d for d in devices if d.get("status") == "online"])
        total_power = sum(d.get("power", 0) for d in devices)
        total_energy_today = sum(d.get("energy", 0) for d in devices)
        average_power = total_power / total_devices if total_devices > 0 else 0
        
        # Get real-time alerts from anomaly detector
        alerts = realtime_detector.get_recent_alerts(limit=5)
        
        # Get alert summary for additional stats
        alert_summary = realtime_detector.get_alert_summary()

        # Convert devices to recent readings format
        recent_readings = []
        for device in devices[:3]:  # Show last 3 devices
            recent_readings.append({
                "id": f"reading-{device.get('id')}",
                "deviceId": device.get("id"),
                "deviceName": device.get("name"),
                "timestamp": device.get("lastSeen"),
                "power": device.get("power", 0),
                "energy": device.get("energy", 0),
                "voltage": device.get("voltage", 0),
                "current": device.get("current", 0),
                "location": device.get("location"),
            })

        dashboard_data = {
            "totalDevices": total_devices,
            "onlineDevices": online_devices,
            "totalEnergyToday": round(total_energy_today, 1),
            "totalEnergyMonth": round(total_energy_today * 30, 1),  # Approximate monthly
            "averagePower": round(average_power, 1),
            "alerts": alerts,
            "alertSummary": alert_summary,
            "recentReadings": recent_readings,
        }
        return success_response(dashboard_data, "Dashboard data retrieved successfully")
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return error_response("Failed to fetch dashboard data", [str(e)])


@router.get("/alerts")
async def get_alerts(limit: int = Query(20, ge=1, le=100)):
    """Get real-time anomaly alerts"""
    try:
        alerts = realtime_detector.get_recent_alerts(limit=limit)
        alert_summary = realtime_detector.get_alert_summary()
        
        return success_response({
            "alerts": alerts,
            "summary": alert_summary
        }, "Alerts retrieved successfully")
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return error_response("Failed to fetch alerts", [str(e)])


@router.post("/alerts/{alert_id}/mark-read")
async def mark_alert_read(alert_id: str):
    """Mark an alert as read"""
    try:
        # Find and mark alert as read
        for alert in realtime_detector.alerts:
            if alert.id == alert_id:
                alert.is_read = True
                return success_response({"alertId": alert_id}, "Alert marked as read")
        
        return error_response("Alert not found", ["Invalid alert ID"])
    except Exception as e:
        logger.error(f"Error marking alert as read: {e}")
        return error_response("Failed to mark alert as read", [str(e)])


@router.get("/consumption/trends")
async def get_consumption_trends(
    interval: str = Query("hourly", regex="^(minutely|hourly|daily)$"),
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    device_id: Optional[str] = None,
):
    """Get energy consumption trends from real InfluxDB data"""
    try:
        # Get real data from InfluxDB
        chart_data = await influx_service.get_chart_data(
            field="energy",
            interval=interval,
            time_range=time_range,
            device_id=device_id
        )
        
        # Return real data or empty array if no data found
        if not chart_data:
            logger.info(f"No real energy data found for interval={interval}, time_range={time_range}")
            return success_response([], "No energy consumption data available for the selected time range")

        return success_response(
            chart_data, f"Energy consumption trends for {interval} interval retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error fetching consumption trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch consumption trends: {str(e)}")


@router.get("/power/trends")
async def get_power_trends(
    interval: str = Query("hourly", regex="^(minutely|hourly|daily)$"),
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    device_id: Optional[str] = None,
):
    """Get power usage trends from real InfluxDB data"""
    try:
        # Get real data from InfluxDB
        chart_data = await influx_service.get_chart_data(
            field="power",
            interval=interval,
            time_range=time_range,
            device_id=device_id
        )
        
        # Return real data or empty array if no data found  
        if not chart_data:
            logger.info(f"No real power data found for interval={interval}, time_range={time_range}")
            return success_response([], "No power usage data available for the selected time range")

        return success_response(
            chart_data, f"Power usage trends for {interval} interval retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error fetching power trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch power trends: {str(e)}")


@router.get("/efficiency/analysis")
async def get_efficiency_analysis():
    """Get energy efficiency analysis"""
    return {
        "overall_efficiency": 82.5,
        "device_efficiency": [
            {"device_id": "device-001", "efficiency": 85.2},
            {"device_id": "device-002", "efficiency": 79.8},
        ],
        "improvement_suggestions": [
            "Optimize device-002 operating hours",
            "Consider upgrading old equipment",
        ],
    }


@router.get("/reports/energy")
async def generate_energy_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    device_ids: Optional[List[str]] = Query(None),
):
    """Generate energy consumption report"""
    return {
        "report_id": "RPT-2024-001",
        "period": f"{start_date} to {end_date}",
        "devices": device_ids or ["all"],
        "total_consumption": 2847.6,
        "total_cost": 426.45,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/forecasting")
async def get_consumption_forecast(days_ahead: int = Query(30, ge=1, le=365)):
    """Get energy consumption forecast"""
    return {
        "forecast_period": f"Next {days_ahead} days",
        "predicted_consumption": 1450.8,
        "confidence_interval": {"lower": 1380.2, "upper": 1521.4},
        "forecast_accuracy": 94.2,
    }
