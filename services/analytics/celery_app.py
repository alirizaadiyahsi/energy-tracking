from celery import Celery
from core.config import settings

celery_app = Celery(
    'analytics',
    broker=settings.CELERY_BROKER_URL,
    include=['tasks.analytics_tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True
)
