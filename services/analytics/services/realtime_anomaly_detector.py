"""
Simplified Real-time Anomaly Detection Service for Analytics
Creates mock anomaly alerts based on IoT mock service triggers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

logger = logging.getLogger(__name__)


class AnomalyAlert:
    """Represents an anomaly alert"""
    
    def __init__(
        self,
        alert_id: str,
        device_id: str,
        device_name: str,
        anomaly_type: str,
        severity: str,
        message: str,
        created_at: datetime
    ):
        self.id = alert_id
        self.device_id = device_id
        self.device_name = device_name
        self.anomaly_type = anomaly_type
        self.severity = severity
        self.message = message
        self.created_at = created_at
        self.is_read = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for API response"""
        return {
            "id": self.id,
            "type": self.severity,
            "title": f"{self.anomaly_type.replace('_', ' ').title()} Alert",
            "message": self.message,
            "deviceId": self.device_id,
            "deviceName": self.device_name,
            "isRead": self.is_read,
            "createdAt": self.created_at.isoformat() + "Z"
        }


class RealtimeAnomalyDetector:
    """Simplified real-time anomaly detection"""
    
    def __init__(self):
        self.alerts: List[AnomalyAlert] = []
        self._running = False
        self._create_initial_alerts()
    
    async def _get_real_devices(self):
        """Get real devices from data ingestion service"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://data-ingestion:8001/api/v1/devices", timeout=5.0)
                devices_data = response.json()
                if devices_data.get("success") and devices_data.get("data"):
                    devices = []
                    for device in devices_data["data"]:
                        devices.append((device.get("id"), device.get("name", "Unknown Device")))
                    return devices
        except Exception as e:
            logger.warning(f"Failed to get real devices: {e}")
        
        # Fallback to some default device patterns if service is unavailable
        return [
            ("mock-hvac-001", "HVAC System - Building A"),
            ("mock-lighting-001", "Lighting System - Floor 2"),
            ("mock-server-001", "Server Room - Rack 1"),
            ("mock-industrial-001", "Industrial Equipment - Line 3"),
            ("mock-appliance-001", "Kitchen Appliances - Main")
        ]

    def _create_initial_alerts(self):
        """Create some initial sample alerts - will be replaced by real device data on first monitoring cycle"""
        # Start with empty alerts list - real alerts will be populated from actual device data
        pass
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        self._running = True
        logger.info("Starting simplified anomaly detection monitoring")
        
        while self._running:
            try:
                await self._check_for_new_anomalies()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in anomaly monitoring loop: {e}")
                await asyncio.sleep(120)  # Wait longer on error
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self._running = False
        logger.info("Stopped anomaly detection monitoring")
    
    async def _check_for_new_anomalies(self):
        """Simulate checking for new anomalies"""
        try:
            # 10% chance to create a new anomaly alert each minute
            if random.random() < 0.1:
                await self._create_random_alert()
        except Exception as e:
            logger.error(f"Error creating new anomaly: {e}")
    
    async def _create_random_alert(self):
        """Create a random anomaly alert using real device data"""
        # Get real devices from data ingestion service
        devices = await self._get_real_devices()
        
        anomaly_types = [
            ("high_power_consumption", "warning", "Detected abnormally high power consumption"),
            ("voltage_fluctuation", "warning", "Voltage readings fluctuating outside normal range"),
            ("power_spike", "warning", "Sudden power spike detected"),
            ("sustained_high_load", "info", "Device running at sustained high load")
        ]
        
        device_id, device_name = random.choice(devices)
        anomaly_type, severity, base_message = random.choice(anomaly_types)
        
        # Check if we already have a recent alert for this device and type
        recent_alerts = [
            alert for alert in self.alerts
            if (alert.device_id == device_id and 
                alert.anomaly_type == anomaly_type and
                (datetime.utcnow() - alert.created_at).total_seconds() < 300)
        ]
        
        if recent_alerts:
            return  # Don't create duplicate alerts
        
        alert_id = f"alert-{device_id}-{anomaly_type}-{int(datetime.utcnow().timestamp())}"
        
        # Get real power/voltage data from the device if available
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://data-ingestion:8001/api/v1/devices/{device_id}", timeout=3.0)
                device_data = response.json()
                if device_data.get("success") and device_data.get("data"):
                    device = device_data["data"]
                    power = device.get("power", 0)
                    voltage = device.get("voltage", 0)
                    current = device.get("current", 0)
                    message = f"{base_message} - Power: {power}W, Voltage: {voltage}V, Current: {current}A"
                else:
                    # Fallback to default values
                    power_values = [23.5, 45.2, 78.9, 120.3, 156.7, 89.4]
                    voltage_values = [235.2, 241.8, 228.9, 246.1, 252.3]
                    message = f"{base_message} - Power: {random.choice(power_values)}W, Voltage: {random.choice(voltage_values)}V"
        except Exception as e:
            logger.warning(f"Failed to get real device data for alert: {e}")
            # Fallback to mock values
            power_values = [23.5, 45.2, 78.9, 120.3, 156.7, 89.4]
            voltage_values = [235.2, 241.8, 228.9, 246.1, 252.3]
            message = f"{base_message} - Power: {random.choice(power_values)}W, Voltage: {random.choice(voltage_values)}V"
        
        alert = AnomalyAlert(
            alert_id=alert_id,
            device_id=device_id,
            device_name=device_name,
            anomaly_type=anomaly_type,
            severity=severity,
            message=message,
            created_at=datetime.utcnow()
        )
        
        self.alerts.append(alert)
        
        # Keep only last 50 alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
        
        logger.warning(f"New anomaly detected: {message}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts for dashboard"""
        recent_alerts = sorted(self.alerts, key=lambda x: x.created_at, reverse=True)[:limit]
        return [alert.to_dict() for alert in recent_alerts]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        recent_alerts = [alert for alert in self.alerts if alert.created_at >= last_24h]
        
        critical_count = len([a for a in recent_alerts if a.severity == "critical"])
        warning_count = len([a for a in recent_alerts if a.severity == "warning"])
        info_count = len([a for a in recent_alerts if a.severity == "info"])
        
        return {
            "total_alerts_24h": len(recent_alerts),
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "info_alerts": info_count,
            "active_anomalies": len([a for a in recent_alerts if not a.is_read])
        }


# Global instance
realtime_detector = RealtimeAnomalyDetector()
