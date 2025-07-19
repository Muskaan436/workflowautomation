from celery import Celery
from app.config import settings

celery_app = Celery(
    "workflow_automation",
    broker=settings.REDIS_CELERY_BROKER,
    backend=settings.REDIS_CELERY_BACKEND,
    include=['app.main_tasks']
)

# Upstash-optimized configuration
celery_app.conf.update(
    # Use Redis as both broker and result backend
    result_backend=settings.REDIS_CELERY_BACKEND,
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    
    # Task routing
    task_routes={
        'app.tasks.*': {'queue': 'default'}
    },
    
    # Worker settings optimized for Upstash
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # Result settings
    result_expires=3600,  # 1 hour
    task_ignore_result=False,
    
    # Connection settings for Upstash
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_connection_timeout=30,
    
    # Windows-specific settings
    worker_pool='solo',  # Use solo pool instead of prefork on Windows
    worker_concurrency=1,
    
    # Beat schedule
    beat_schedule={
        "poll-notion-every-5-minutes": {
            "task": "app.main_tasks.poll_notion_and_schedule_meetings",
            "schedule": 300.0,  # 5 minutes = 300 seconds
        },
    }
)
