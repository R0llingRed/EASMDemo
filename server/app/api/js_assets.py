"""JS asset API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import js_asset as crud_js_asset
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.js_api import JSAssetOut

router = APIRouter(prefix="/projects/{project_id}/js-assets", tags=["js-assets"])


@router.get("", response_model=Page[JSAssetOut])
def list_project_js_assets(
    script_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 500:
        limit = 100

    items = crud_js_asset.list_js_assets(
        db=db,
        project_id=project.id,
        script_type=script_type,
        skip=skip,
        limit=limit,
    )
    total = crud_js_asset.count_js_assets(
        db=db,
        project_id=project.id,
        script_type=script_type,
    )
    return Page(items=items, total=total)


@router.get("/{js_asset_id}", response_model=JSAssetOut)
def get_project_js_asset(
    js_asset_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    js_asset = crud_js_asset.get_js_asset(db=db, js_asset_id=js_asset_id)
    if not js_asset or js_asset.project_id != project.id:
        raise HTTPException(status_code=404, detail="JS asset not found")
    return js_asset
