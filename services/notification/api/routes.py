from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class NotificationRequest(BaseModel):
    recipient: EmailStr
    subject: str
    message: str
    notification_type: str = "info"

class AlertRequest(BaseModel):
    device_id: str
    alert_type: str
    severity: str
    message: str
    recipients: List[EmailStr]

@router.post("/send")
async def send_notification(notification: NotificationRequest):
    """Send a notification via email"""
    logger.info(f"Sending notification to {notification.recipient}")
    
    # Simulate sending notification
    return {
        "status": "sent",
        "recipient": notification.recipient,
        "subject": notification.subject,
        "sent_at": datetime.utcnow().isoformat()
    }

@router.post("/alerts")
async def send_alert(alert: AlertRequest):
    """Send an alert to multiple recipients"""
    logger.info(f"Sending alert for device {alert.device_id}")
    
    results = []
    for recipient in alert.recipients:
        results.append({
            "recipient": recipient,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat()
        })
    
    return {
        "alert_id": f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "device_id": alert.device_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "recipients_notified": len(results),
        "results": results
    }

@router.get("/templates")
async def get_notification_templates():
    """Get available notification templates"""
    return {
        "templates": [
            {
                "id": "energy_alert",
                "name": "Energy Consumption Alert",
                "description": "Alert for high energy consumption"
            },
            {
                "id": "device_offline",
                "name": "Device Offline Alert",
                "description": "Alert when device goes offline"
            },
            {
                "id": "anomaly_detected",
                "name": "Anomaly Detection Alert",
                "description": "Alert for detected anomalies"
            }
        ]
    }

@router.get("/history")
async def get_notification_history(
    limit: int = 100,
    offset: int = 0
):
    """Get notification history"""
    return {
        "notifications": [
            {
                "id": "NOT-001",
                "recipient": "user@example.com",
                "subject": "Energy Alert",
                "status": "sent",
                "created_at": "2024-01-01T10:00:00Z",
                "sent_at": "2024-01-01T10:01:00Z"
            }
        ],
        "total": 1,
        "limit": limit,
        "offset": offset
    }
