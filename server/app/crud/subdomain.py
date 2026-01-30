from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from server.app.models.subdomain import Subdomain
from server.app.utils.fingerprint import compute_subdomain_fingerprint


def upsert_subdomain(
    db: Session,
    project_id: UUID,
    root_domain: str,
    subdomain: str,
    source: str,
    ip_addresses: Optional[List[str]] = None,
    cname: Optional[str] = None,
) -> Subdomain:
    fingerprint = compute_subdomain_fingerprint(str(project_id), subdomain)
    stmt = insert(Subdomain).values(
        project_id=project_id,
        root_domain=root_domain,
        subdomain=subdomain,
        source=source,
        ip_addresses=ip_addresses or [],
        cname=cname,
        fingerprint_hash=fingerprint,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["project_id", "subdomain"],
        set_={
            "ip_addresses": stmt.excluded.ip_addresses,
            "cname": stmt.excluded.cname,
            "last_seen": func.now(),
        },
        where=(Subdomain.project_id == stmt.excluded.project_id),
    )
    db.execute(stmt)
    db.commit()
    result = db.scalars(
        select(Subdomain).where(
            Subdomain.project_id == project_id,
            Subdomain.subdomain == subdomain,
        )
    ).first()
    return result


def bulk_upsert_subdomains(
    db: Session,
    project_id: UUID,
    root_domain: str,
    subdomains: List[str],
    source: str,
) -> int:
    if not subdomains:
        return 0
    values = [
        {
            "project_id": project_id,
            "root_domain": root_domain,
            "subdomain": sub,
            "source": source,
            "ip_addresses": [],
            "fingerprint_hash": compute_subdomain_fingerprint(str(project_id), sub),
        }
        for sub in subdomains
    ]
    stmt = insert(Subdomain).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["project_id", "subdomain"],
        set_={"last_seen": func.now()},
        where=(Subdomain.project_id == stmt.excluded.project_id),
    )
    db.execute(stmt)
    db.commit()
    return len(subdomains)


def list_subdomains(
    db: Session,
    project_id: UUID,
    root_domain: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Subdomain]:
    stmt = select(Subdomain).where(Subdomain.project_id == project_id)
    if root_domain:
        stmt = stmt.where(Subdomain.root_domain == root_domain)
    stmt = stmt.order_by(Subdomain.subdomain).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_subdomains(
    db: Session,
    project_id: UUID,
    root_domain: Optional[str] = None,
) -> int:
    stmt = select(func.count()).select_from(Subdomain).where(Subdomain.project_id == project_id)
    if root_domain:
        stmt = stmt.where(Subdomain.root_domain == root_domain)
    return db.scalar(stmt) or 0
