from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud.asset_entity import bulk_import_assets, list_assets
from server.app.db.session import get_db
from server.app.schemas.asset_entity import AssetEntityOut, AssetImportRequest, AssetImportResult
from server.app.schemas.common import Page

router = APIRouter(prefix="/projects/{project_id}/assets", tags=["assets"])


@router.post("/import", response_model=AssetImportResult)
def import_assets(
    payload: AssetImportRequest,
    project=Depends(get_project_dep),
    db: Session = Depends(get_db),
) -> AssetImportResult:
    inserted, skipped, total = bulk_import_assets(
        db,
        project_id=project.id,
        assets=[asset.model_dump() for asset in payload.assets],
    )
    return AssetImportResult(inserted=inserted, skipped=skipped, total=total)


@router.get("", response_model=Page[AssetEntityOut])
def list_assets_endpoint(
    asset_type: str | None = None,
    offset: int = 0,
    limit: int = 20,
    project=Depends(get_project_dep),
    db: Session = Depends(get_db),
) -> Page[AssetEntityOut]:
    total, items = list_assets(
        db, project_id=project.id, asset_type=asset_type, offset=offset, limit=limit
    )
    return Page(total=total, items=items)
