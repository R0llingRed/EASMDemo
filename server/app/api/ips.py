from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud.ip_address import list_ip_addresses
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.ip_address import IPAddressOut

router = APIRouter(prefix="/projects/{project_id}/ips", tags=["ips"])


@router.get("", response_model=Page[IPAddressOut])
def list_project_ips(
    skip: int = 0,
    limit: int = 100,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 500:
        limit = 100
    items = list_ip_addresses(
        db=db,
        project_id=project.id,
        skip=skip,
        limit=limit,
    )
    return Page(items=items, total=len(items), skip=skip, limit=limit)
