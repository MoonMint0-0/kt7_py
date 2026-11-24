import logging
from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "task_tracker_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="tasks.notify_task_created")
def notify_task_created(task_id: int, title: str, project_id: int, creator_id: int) -> dict:
    message = (
        f"Создана задача #{task_id} ('{title}') в проекте #{project_id} "
        f"пользователем #{creator_id}"
    )
    logger.info(message)
    return {"status": "notified", "detail": message}