from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.crud.ip_address import get_ip_address
from server.app.crud.port import list_ports_by_ip
from server.app.db.session import get_db
from server.app.schemas.common import Page
from server.app.schemas.port import PortOut

router = APIRouter(prefix="/ips/{ip_id}/ports", tags=["ports"])


@router.get("", response_model=Page[PortOut])
def list_ip_ports(
    ip_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    ip_obj = get_ip_address(db, ip_id)
    if not ip_obj:
        raise HTTPException(status_code=404, detail="IP not found")
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 500:
        limit = 100
    items = list_ports_by_ip(db=db, ip_id=ip_id, skip=skip, limit=limit)
    return Page(items=items, total=len(items), skip=skip, limit=limit)
