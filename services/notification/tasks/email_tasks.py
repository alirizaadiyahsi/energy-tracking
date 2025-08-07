from celery import Celery
from celery.result import AsyncResult
from core.config import settings
from services.email_service import EmailService
from typing import Dict, Any
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_CELERY}" if settings.REDIS_PASSWORD else f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_CELERY}"

celery_app = Celery(
    "notification_worker",
    broker=redis_url,
    backend=redis_url
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
        
        # Update notification status in database (import here to avoid initialization issues)
        try:
            from models.notification import Notification
            from core.database import get_sync_db
            
            db = next(get_sync_db())
            try:
                notification = db.query(Notification).filter(Notification.id == notification_id).first()
                if notification:
                    if success:
                        notification.status = "sent"
                        notification.sent_at = datetime.utcnow()
                    else:
                        notification.status = "failed"
                    db.commit()
                    logger.info(f"Updated notification {notification_id} status to {notification.status}")
            except Exception as db_error:
                db.rollback()
                logger.error(f"Database error updating notification {notification_id}: {db_error}")
            finally:
                db.close()
        except Exception as import_error:
            logger.warning(f"Could not update database for notification {notification_id}: {import_error}")
        
        if success:
            logger.info(f"Email notification {notification_id} sent successfully")
            return {"status": "success", "notification_id": notification_id}
        else:
            logger.error(f"Failed to send email notification {notification_id}")
            return {"status": "failed", "notification_id": notification_id}
            
    except Exception as e:
        logger.error(f"Error processing email notification: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def send_bulk_notifications(self, notifications_data: list):
    """
    Send multiple notifications in bulk
    """
    try:
        logger.info(f"Processing bulk notifications: {len(notifications_data)} items")
        
        results = []
        for notification_data in notifications_data:
            try:
                result = send_email_notification.delay(notification_data)
                results.append({
                    "notification_id": notification_data.get("id"),
                    "task_id": result.id,
                    "status": "queued"
                })
            except Exception as e:
                logger.error(f"Error queuing notification {notification_data.get('id')}: {e}")
                results.append({
                    "notification_id": notification_data.get("id"),
                    "status": "failed",
                    "error": str(e)
                })
        
        return {"status": "completed", "results": results}
        
    except Exception as e:
        logger.error(f"Error processing bulk notifications: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task
def process_pending_notifications():
    """
    Process all pending notifications
    """
    try:
        logger.info("Processing pending notifications")
        
        # Import here to avoid initialization issues
        from models.notification import Notification
        from core.database import get_sync_db
        
        db = next(get_sync_db())
        try:
            pending_notifications = db.query(Notification).filter(
                Notification.status == "pending"
            ).all()
            
            if not pending_notifications:
                logger.info("No pending notifications found")
                return {"status": "completed", "processed": 0}
            
            logger.info(f"Found {len(pending_notifications)} pending notifications")
            
            processed = 0
            for notification in pending_notifications:
                try:
                    notification_data = {
                        "id": notification.id,
                        "recipient": notification.recipient,
                        "subject": notification.subject,
                        "message": notification.message,
                        "template_data": json.loads(notification.template_data) if notification.template_data else None
                    }
                    
                    send_email_notification.delay(notification_data)
                    processed += 1
                    logger.info(f"Queued notification {notification.id}")
                    
                except Exception as e:
                    logger.error(f"Error queuing notification {notification.id}: {e}")
            
            logger.info(f"Processed {processed} notifications")
            return {"status": "completed", "processed": processed}
            
        except Exception as db_error:
            logger.error(f"Database error processing pending notifications: {db_error}")
            return {"status": "error", "error": str(db_error)}
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error processing pending notifications: {str(e)}")
        return {"status": "error", "error": str(e)}


@celery_app.task
def cleanup_old_notifications(days: int = 30):
    """
    Clean up old notifications older than specified days
    """
    try:
        from models.notification import Notification
        from core.database import get_sync_db
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        logger.info(f"Cleaning up notifications older than {cutoff_date}")
        
        db = next(get_sync_db())
        try:
            deleted_count = db.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return {"status": "completed", "deleted_count": deleted_count}
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error during cleanup: {db_error}")
            return {"status": "error", "error": str(db_error)}
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return {"status": "error", "error": str(e)}


# Health check task
@celery_app.task
def health_check():
    """
    Simple health check task for monitoring
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
