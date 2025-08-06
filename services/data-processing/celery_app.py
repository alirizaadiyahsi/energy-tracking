from celery import Celery
from core.config import settings

# Create Celery instance
celery_app = Celery(
    'data-processing',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['tasks.processing_tasks']
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        'hourly-aggregation': {
            'task': 'tasks.processing_tasks.run_hourly_aggregation',
            'schedule': 3600.0,  # Run every hour
        },
        'daily-anomaly-detection': {
            'task': 'tasks.processing_tasks.run_anomaly_detection',
            'schedule': 86400.0,  # Run daily
        },
        'weekly-cleanup': {
            'task': 'tasks.processing_tasks.run_data_cleanup',
            'schedule': 604800.0,  # Run weekly
        },
    },
)

if __name__ == '__main__':
    celery_app.start()
