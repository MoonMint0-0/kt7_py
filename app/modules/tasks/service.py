import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.projects.models import Project
from app.modules.tasks.models import Task
from app.modules.tasks.schemas import TaskCreate, TaskUpdate
from app.modules.users.models import User
from app.tasks_worker.celery_app import notify_task_created

logger = logging.getLogger(__name__)


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена",
        )
    return task


def list_tasks(
    db: Session,
    current_user: User,
    project_id: int | None = None,
) -> list[Task]:
    query = db.query(Task)
    if current_user.role != "admin":
        query = query.filter(Task.creator_id == current_user.id)
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    return query.order_by(Task.id).all()


def create_task(db: Session, payload: TaskCreate, current_user: User) -> Task:
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанный проект не найден",
        )
    if project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя создавать задачи в чужом проекте",
        )

    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        project_id=payload.project_id,
        creator_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        notify_task_created.delay(
            task_id=task.id,
            title=task.title,
            project_id=task.project_id,
            creator_id=task.creator_id,
        )
    except Exception as exc:
        logger.warning("Не удалось поставить задачу Celery в очередь: %s", exc)

    return task


def update_task(
    db: Session,
    task_id: int,
    payload: TaskUpdate,
    current_user: User,
) -> Task:
    task = get_task_or_404(db, task_id)
    if task.creator_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на изменение этой задачи",
        )

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.status is not None:
        task.status = payload.status

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int, current_user: User) -> None:
    task = get_task_or_404(db, task_id)
    if task.creator_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на удаление этой задачи",
        )

    db.delete(task)
    db.commit()