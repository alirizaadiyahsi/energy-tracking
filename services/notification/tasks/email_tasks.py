from celery import Celery
from celery.result import AsyncResult
from core.config import settings
from services.email_service import EmailService
from models.notification import Notification
from core.database import get_db
from typing import Dict, Any
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "notification_worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_CELERY}",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_CELERY}"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
)


@celery_app.task(bind=True)
def send_email_notification(self, notification_data: Dict[str, Any]):
    """
    Send email notification task
    """
    try:
        notification_id = notification_data.get("id")
        logger.info(f"Processing email notification {notification_id}")
        
        # Create email service
        email_service = EmailService()
        
        # Send email
        success = email_service.send_email(
            recipient=notification_data["recipient"],
            subject=notification_data["subject"],
            message=notification_data["message"],
            template_data=notification_data.get("template_data")
        )
        
        # Update notification status in database
        db = next(get_db())
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if notification:
                if success:
                    notification.status = "sent"
                    notification.sent_at = datetime.utcnow()
                    logger.info(f"Email notification {notification_id} sent successfully")
                else:
                    notification.status = "failed"
                    notification.error_message = "Failed to send email"
                    logger.error(f"Failed to send email notification {notification_id}")
                
                db.commit()
        finally:
            db.close()
        
        return {"success": success, "notification_id": notification_id}
        
    except Exception as exc:
        logger.error(f"Error sending email notification: {exc}")
        # Retry task
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def send_bulk_notifications(self, notifications_data: list):
    """
    Send multiple notifications in bulk
    """
    results = []
    for notification_data in notifications_data:
        try:
            # Send individual notification
            result = send_email_notification.delay(notification_data)
            results.append({
                "notification_id": notification_data.get("id"),
                "task_id": result.id,
                "status": "queued"
            })
        except Exception as exc:
            logger.error(f"Error queuing notification {notification_data.get('id')}: {exc}")
            results.append({
                "notification_id": notification_data.get("id"),
                "error": str(exc),
                "status": "failed"
            })
    
    return results


@celery_app.task
def process_scheduled_notifications():
    """
    Process scheduled notifications that need to be sent
    """
    try:
        db = next(get_db())
        
        # Get pending notifications
        pending_notifications = db.query(Notification).filter(
            Notification.status == "pending"
        ).limit(100).all()
        
        logger.info(f"Processing {len(pending_notifications)} pending notifications")
        
        for notification in pending_notifications:
            notification_data = {
                "id": notification.id,
                "recipient": notification.recipient,
                "subject": notification.subject,
                "message": notification.message,
                "template_data": json.loads(notification.template_data) if notification.template_data else None
            }
            
            # Queue notification for sending
            send_email_notification.delay(notification_data)
            
        db.close()
        
    except Exception as exc:
        logger.error(f"Error processing scheduled notifications: {exc}")
        raise exc


@celery_app.task
def cleanup_old_notifications():
    """
    Clean up old notifications and logs
    """
    try:
        from datetime import timedelta
        
        db = next(get_db())
        
        # Delete notifications older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        deleted_count = db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete()
        
        db.commit()
        db.close()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        
        return {"deleted_count": deleted_count}
        
    except Exception as exc:
        logger.error(f"Error cleaning up notifications: {exc}")
        raise exc


def get_task_status(task_id: str):
    """
    Get the status of a Celery task
    """
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result,
        "traceback": result.traceback
    }
