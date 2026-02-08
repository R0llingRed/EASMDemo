from typing import Iterable, List, Tuple

from sqlalchemy import delete, func, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from server.app.models.asset_entity import AssetEntity
from server.app.schemas.asset_entity import AssetType


def bulk_import_assets(
    db: Session, project_id, assets: Iterable[dict]
) -> Tuple[int, int, int]:
    asset_list = list(assets)
    if not asset_list:
        return 0, 0, 0

    deduped = {}
    for asset in asset_list:
        key = (asset["asset_type"], asset["value"])
        if key not in deduped:
            deduped[key] = asset

    pairs = list(deduped.keys())
    total = len(asset_list)
    if not pairs:
        return 0, total, total

    existing = (
        db.scalar(
            select(func.count())
            .select_from(AssetEntity)
            .where(AssetEntity.project_id == project_id)
            .where(tuple_(AssetEntity.asset_type, AssetEntity.value).in_(pairs))
        )
        or 0
    )

    stmt = insert(AssetEntity).values(
        [
            {
                "project_id": project_id,
                "asset_type": asset["asset_type"],
                "value": asset["value"],
                "source": asset.get("source"),
            }
            for asset in deduped.values()
        ]
    )
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["project_id", "asset_type", "value"]
    )
    db.execute(stmt)
    db.execute(
        update(AssetEntity)
        .where(AssetEntity.project_id == project_id)
        .where(tuple_(AssetEntity.asset_type, AssetEntity.value).in_(pairs))
        .values(last_seen=func.now())
    )
    db.commit()

    inserted = max(len(pairs) - existing, 0)
    skipped = total - inserted
    return inserted, skipped, total


def list_assets(
    db: Session, project_id, asset_type: AssetType | None, offset: int, limit: int
) -> Tuple[int, List[AssetEntity]]:
    query = select(AssetEntity).where(AssetEntity.project_id == project_id)
    if asset_type:
        query = query.where(AssetEntity.asset_type == asset_type)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = (
        db.scalars(query.order_by(AssetEntity.first_seen.desc()).offset(offset).limit(limit))
        .all()
    )
    return total, items


def get_asset(db: Session, asset_id) -> AssetEntity | None:
    return db.get(AssetEntity, asset_id)


def update_asset_source(
    db: Session,
    asset: AssetEntity,
    source: str | None,
) -> AssetEntity:
    asset.source = source
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset: AssetEntity) -> None:
    db.execute(delete(AssetEntity).where(AssetEntity.id == asset.id))
    db.commit()
