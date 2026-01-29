from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.app.crud.project import get_project
from server.app.db.session import get_db
from server.app.models.project import Project


def get_project_dep(project_id: UUID, db: Session = Depends(get_db)) -> Project:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    return project
