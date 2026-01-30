from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from server.app.models.web_asset import WebAsset
from server.app.utils.fingerprint import compute_url_fingerprint


def upsert_web_asset(
    db: Session,
    project_id: UUID,
    url: str,
    **kwargs,
) -> WebAsset:
    fingerprint = compute_url_fingerprint(str(project_id), url)
    stmt = insert(WebAsset).values(
        project_id=project_id,
        url=url,
        fingerprint_hash=fingerprint,
        **kwargs,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["project_id", "url"],
        set_={
            "title": stmt.excluded.title,
            "status_code": stmt.excluded.status_code,
            "content_length": stmt.excluded.content_length,
            "content_type": stmt.excluded.content_type,
            "server": stmt.excluded.server,
            "technologies": stmt.excluded.technologies,
            "fingerprints": stmt.excluded.fingerprints,
            "headers": stmt.excluded.headers,
            "screenshot_path": stmt.excluded.screenshot_path,
            "is_alive": stmt.excluded.is_alive,
            "last_seen": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()
    return db.scalars(
        select(WebAsset).where(
            WebAsset.project_id == project_id,
            WebAsset.url == url,
        )
    ).first()


def get_web_asset(db: Session, asset_id: UUID) -> Optional[WebAsset]:
    return db.get(WebAsset, asset_id)


def list_web_assets(
    db: Session,
    project_id: UUID,
    status_code: Optional[int] = None,
    is_alive: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[WebAsset]:
    stmt = select(WebAsset).where(WebAsset.project_id == project_id)
    if status_code is not None:
        stmt = stmt.where(WebAsset.status_code == status_code)
    if is_alive is not None:
        stmt = stmt.where(WebAsset.is_alive == is_alive)
    stmt = stmt.order_by(WebAsset.url).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_web_assets(
    db: Session,
    project_id: UUID,
    status_code: Optional[int] = None,
    is_alive: Optional[bool] = None,
) -> int:
    stmt = select(func.count()).select_from(WebAsset).where(WebAsset.project_id == project_id)
    if status_code is not None:
        stmt = stmt.where(WebAsset.status_code == status_code)
    if is_alive is not None:
        stmt = stmt.where(WebAsset.is_alive == is_alive)
    return db.scalar(stmt) or 0
