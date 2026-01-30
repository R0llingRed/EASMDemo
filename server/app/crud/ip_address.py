from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from server.app.models.ip_address import IPAddress


def upsert_ip_address(
    db: Session,
    project_id: UUID,
    ip: str,
    source: str,
) -> IPAddress:
    stmt = insert(IPAddress).values(
        project_id=project_id,
        ip=ip,
        source=source,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["project_id", "ip"],
        set_={"last_seen": func.now()},
        where=(IPAddress.project_id == stmt.excluded.project_id),
    )
    db.execute(stmt)
    db.commit()
    result = db.scalars(
        select(IPAddress).where(
            IPAddress.project_id == project_id,
            IPAddress.ip == ip,
        )
    ).first()
    return result


def get_ip_address(db: Session, ip_id: UUID) -> Optional[IPAddress]:
    return db.get(IPAddress, ip_id)


def get_ip_by_value(db: Session, project_id: UUID, ip: str) -> Optional[IPAddress]:
    return db.scalars(
        select(IPAddress).where(
            IPAddress.project_id == project_id,
            IPAddress.ip == ip,
        )
    ).first()


def list_ip_addresses(
    db: Session,
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[IPAddress]:
    stmt = (
        select(IPAddress)
        .where(IPAddress.project_id == project_id)
        .order_by(IPAddress.ip)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def count_ip_addresses(db: Session, project_id: UUID) -> int:
    stmt = select(func.count()).select_from(IPAddress).where(IPAddress.project_id == project_id)
    return db.scalar(stmt) or 0
