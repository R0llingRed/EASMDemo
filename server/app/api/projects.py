from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from server.app.crud.project import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from server.app.db.session import get_db
from server.app.schemas.common import Page
from server.app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectOut:
    try:
        return create_project(db, name=payload.name, description=payload.description)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="project already exists") from exc
    except ProgrammingError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="database not initialized, run: alembic -c server/alembic.ini upgrade head",
        ) from exc


@router.get("", response_model=Page[ProjectOut])
def list_projects_endpoint(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Page[ProjectOut]:
    total, items = list_projects(db, offset=offset, limit=limit)
    return Page(total=total, items=items)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project_endpoint(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectOut:
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    try:
        return update_project(
            db=db,
            project=project,
            name=payload.name.strip() if payload.name else None,
            description=payload.description,
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="project already exists") from exc


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    deleted = delete_project(db=db, project_id=project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="project not found")
    return None
