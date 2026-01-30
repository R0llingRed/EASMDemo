from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud.subdomain import count_subdomains, list_subdomains
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.subdomain import SubdomainOut

router = APIRouter(prefix="/projects/{project_id}/subdomains", tags=["subdomains"])


@router.get("", response_model=Page[SubdomainOut])
def list_project_subdomains(
    root_domain: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 500:
        limit = 100
    items = list_subdomains(
        db=db,
        project_id=project.id,
        root_domain=root_domain,
        skip=skip,
        limit=limit,
    )
    total = count_subdomains(db=db, project_id=project.id, root_domain=root_domain)
    return Page(items=items, total=total, skip=skip, limit=limit)
