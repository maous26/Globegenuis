from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app - IMPORTANT: la variable doit s'appeler 'app' ou 'celery'
app = Celery(
    "globegenius",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.flight_tasks", "app.tasks.email_tasks"]
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Configure periodic tasks
app.conf.beat_schedule = {
    # Tier 1 routes - every 2 hours
    "scan-tier-1-routes": {
        "task": "app.tasks.flight_tasks.scan_tier_routes",
        "schedule": crontab(minute=0, hour="*/2"),
        "args": (1,)
    },
    # Tier 2 routes - every 4 hours
    "scan-tier-2-routes": {
        "task": "app.tasks.flight_tasks.scan_tier_routes",
        "schedule": crontab(minute=15, hour="*/4"),
        "args": (2,)
    },
    # Tier 3 routes - every 6 hours
    "scan-tier-3-routes": {
        "task": "app.tasks.flight_tasks.scan_tier_routes",
        "schedule": crontab(minute=30, hour="*/6"),
        "args": (3,)
    },
    # Process and send alerts - every 30 minutes
    "process-alerts": {
        "task": "app.tasks.email_tasks.process_pending_alerts",
        "schedule": crontab(minute="*/30")
    },
    # Clean expired deals - daily at 3 AM
    "clean-expired-deals": {
        "task": "app.tasks.flight_tasks.clean_expired_deals",
        "schedule": crontab(hour=3, minute=0)
    },
}

# Important: expose the app
celery = app

if __name__ == "__main__":
    app.start()