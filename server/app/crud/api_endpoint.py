"""CRUD operations for discovered API endpoints."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from server.app.models.api_endpoint import APIEndpoint


def upsert_api_endpoint(
    db: Session,
    project_id: UUID,
    endpoint: str,
    method: str = "GET",
    js_asset_id: Optional[UUID] = None,
    host: Optional[str] = None,
    source: str = "js_analysis",
    requires_auth: Optional[bool] = None,
    risk_tags: Optional[list[str]] = None,
    evidence: Optional[dict] = None,
) -> APIEndpoint:
    """Insert or update discovered endpoint by unique key."""
    normalized_method = (method or "GET").upper()
    stmt = insert(APIEndpoint).values(
        project_id=project_id,
        js_asset_id=js_asset_id,
        endpoint=endpoint,
        method=normalized_method,
        host=host,
        source=source,
        requires_auth=requires_auth,
        risk_tags=risk_tags or [],
        evidence=evidence or {},
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["project_id", "endpoint", "method"],
        set_={
            "js_asset_id": stmt.excluded.js_asset_id,
            "host": stmt.excluded.host,
            "requires_auth": stmt.excluded.requires_auth,
            "risk_tags": stmt.excluded.risk_tags,
            "evidence": stmt.excluded.evidence,
            "last_seen": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()
    return db.scalars(
        select(APIEndpoint).where(
            APIEndpoint.project_id == project_id,
            APIEndpoint.endpoint == endpoint,
            APIEndpoint.method == normalized_method,
        )
    ).first()


def get_api_endpoint(db: Session, endpoint_id: UUID) -> Optional[APIEndpoint]:
    return db.get(APIEndpoint, endpoint_id)


def list_api_endpoints(
    db: Session,
    project_id: UUID,
    method: Optional[str] = None,
    host: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[APIEndpoint]:
    stmt = select(APIEndpoint).where(APIEndpoint.project_id == project_id)
    if method:
        stmt = stmt.where(APIEndpoint.method == method.upper())
    if host:
        stmt = stmt.where(APIEndpoint.host == host)
    stmt = stmt.order_by(APIEndpoint.last_seen.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_api_endpoints(
    db: Session,
    project_id: UUID,
    method: Optional[str] = None,
    host: Optional[str] = None,
) -> int:
    stmt = select(func.count()).select_from(APIEndpoint).where(APIEndpoint.project_id == project_id)
    if method:
        stmt = stmt.where(APIEndpoint.method == method.upper())
    if host:
        stmt = stmt.where(APIEndpoint.host == host)
    return db.scalar(stmt) or 0
