from typing import Iterable, List, Tuple

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from server.app.models.asset_entity import AssetEntity


def bulk_import_assets(
    db: Session, project_id, assets: Iterable[dict]
) -> Tuple[int, int, int]:
    asset_list = list(assets)
    if not asset_list:
        return 0, 0, 0

    stmt = insert(AssetEntity).values(
        [
            {
                "project_id": project_id,
                "asset_type": asset["asset_type"],
                "value": asset["value"],
                "source": asset.get("source"),
            }
            for asset in asset_list
        ]
    )
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["project_id", "asset_type", "value"]
    )
    result = db.execute(stmt)
    db.commit()
    inserted = result.rowcount or 0
    total = len(asset_list)
    skipped = total - inserted
    return inserted, skipped, total


def list_assets(
    db: Session, project_id, asset_type: str | None, offset: int, limit: int
) -> Tuple[int, List[AssetEntity]]:
    query = select(AssetEntity).where(AssetEntity.project_id == project_id)
    if asset_type:
        query = query.where(AssetEntity.asset_type == asset_type)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(AssetEntity.first_seen.desc()).offset(offset).limit(limit)).all()
    return total, items
