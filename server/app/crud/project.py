from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from server.app.models.project import Project


def create_project(db: Session, name: str, description: str | None) -> Project:
    project = Project(name=name, description=description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id) -> Project | None:
    return db.get(Project, project_id)


def list_projects(db: Session, offset: int, limit: int) -> Tuple[int, List[Project]]:
    total = db.scalar(select(func.count()).select_from(Project)) or 0
    items = db.scalars(select(Project).offset(offset).limit(limit)).all()
    return total, items
