from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud.web_asset import count_web_assets, get_web_asset, list_web_assets
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.web_asset import WebAssetOut

router = APIRouter(prefix="/projects/{project_id}/web-assets", tags=["web-assets"])


@router.get("", response_model=Page[WebAssetOut])
def list_project_web_assets(
    status_code: Optional[int] = None,
    is_alive: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 500:
        limit = 100
    items = list_web_assets(
        db=db,
        project_id=project.id,
        status_code=status_code,
        is_alive=is_alive,
        skip=skip,
        limit=limit,
    )
    total = count_web_assets(
        db=db,
        project_id=project.id,
        status_code=status_code,
        is_alive=is_alive,
    )
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{asset_id}", response_model=WebAssetOut)
def get_project_web_asset(
    asset_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    asset = get_web_asset(db=db, asset_id=asset_id)
    if not asset or asset.project_id != project.id:
        raise HTTPException(status_code=404, detail="Web asset not found")
    return asset
