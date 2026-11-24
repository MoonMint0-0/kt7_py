from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.projects.models import Project
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.users.models import User


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден",
        )
    return project


def list_projects(db: Session, current_user: User) -> list[Project]:
    if current_user.role == "admin":
        return db.query(Project).order_by(Project.id).all()
    return (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.id)
        .all()
    )


def create_project(db: Session, payload: ProjectCreate, current_user: User) -> Project:
    project = Project(
        title=payload.title,
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(
    db: Session,
    project_id: int,
    payload: ProjectUpdate,
    current_user: User,
) -> Project:
    project = get_project_or_404(db, project_id)
    if project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на изменение этого проекта",
        )

    if payload.title is not None:
        project.title = payload.title
    if payload.description is not None:
        project.description = payload.description

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, current_user: User) -> None:
    project = get_project_or_404(db, project_id)
    if project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на удаление этого проекта",
        )

    db.delete(project)
    db.commit()