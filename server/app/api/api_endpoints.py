"""API endpoint routes for JS deep analysis."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import api_endpoint as crud_api_endpoint
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.js_api import APIEndpointOut

router = APIRouter(prefix="/projects/{project_id}/api-endpoints", tags=["api-endpoints"])


@router.get("", response_model=Page[APIEndpointOut])
def list_project_api_endpoints(
    method: Optional[str] = None,
    host: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 500:
        limit = 100

    items = crud_api_endpoint.list_api_endpoints(
        db=db,
        project_id=project.id,
        method=method,
        host=host,
        skip=skip,
        limit=limit,
    )
    total = crud_api_endpoint.count_api_endpoints(
        db=db,
        project_id=project.id,
        method=method,
        host=host,
    )
    return Page(items=items, total=total)


@router.get("/{endpoint_id}", response_model=APIEndpointOut)
def get_project_api_endpoint(
    endpoint_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    endpoint = crud_api_endpoint.get_api_endpoint(db=db, endpoint_id=endpoint_id)
    if not endpoint or endpoint.project_id != project.id:
        raise HTTPException(status_code=404, detail="API endpoint not found")
    return endpoint
