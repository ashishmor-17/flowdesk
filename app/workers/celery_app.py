from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "flowdesk_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "check-overdue-tasks-every-5-min": {
        "task": "check_overdue_tasks",
        "schedule": 300.0,
    },
    "cleanup-expired-upload-sessions-hourly": {
        "task": "cleanup_expired_upload_sessions",
        "schedule": 3600.0,
    }
}