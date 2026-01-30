from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from server.app.models.port import Port


def upsert_port(
    db: Session,
    ip_id: UUID,
    port: int,
    protocol: str = "tcp",
    state: Optional[str] = None,
    service: Optional[str] = None,
    version: Optional[str] = None,
    banner: Optional[str] = None,
) -> Port:
    stmt = insert(Port).values(
        ip_id=ip_id,
        port=port,
        protocol=protocol,
        state=state,
        service=service,
        version=version,
        banner=banner,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["ip_id", "port", "protocol"],
        set_={
            "state": stmt.excluded.state,
            "service": stmt.excluded.service,
            "version": stmt.excluded.version,
            "banner": stmt.excluded.banner,
            "last_seen": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()
    result = db.scalars(
        select(Port).where(
            Port.ip_id == ip_id,
            Port.port == port,
            Port.protocol == protocol,
        )
    ).first()
    return result


def list_ports_by_ip(
    db: Session,
    ip_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[Port]:
    stmt = (
        select(Port)
        .where(Port.ip_id == ip_id)
        .order_by(Port.port)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
