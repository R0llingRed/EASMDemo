import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud.asset_entity import bulk_import_assets, list_assets
from server.app.db.session import get_db
from server.app.schemas.asset_entity import (
    AssetEntityOut,
    AssetImportRequest,
    AssetImportResult,
    AssetType,
)
from server.app.schemas.common import Page
from worker.app.tasks import event_handler

router = APIRouter(prefix="/projects/{project_id}/assets", tags=["assets"])
logger = logging.getLogger(__name__)


def _asset_type_value(raw_type: object) -> str:
    if hasattr(raw_type, "value"):
        value = getattr(raw_type, "value")
        return str(value).strip().lower()
    return str(raw_type).strip().lower()


def _guess_root_domain(domain: str) -> str:
    parts = [part for part in domain.strip().lower().split(".") if part]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain.strip().lower()


def _normalize_url(value: str) -> str:
    url = value.strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"http://{url}"
    return url


def _sync_assets_for_scan(
    db: Session,
    project_id,
    assets: list[dict],
) -> None:
    from server.app.crud.ip_address import upsert_ip_address
    from server.app.crud.subdomain import upsert_subdomain
    from server.app.crud.web_asset import upsert_web_asset

    deduped = {}
    for asset in assets:
        asset_type = _asset_type_value(asset.get("asset_type"))
        value = str(asset.get("value", "")).strip()
        if not asset_type or not value:
            continue
        deduped[(asset_type, value)] = asset

    for asset_type, value in deduped:
        source = str(deduped[(asset_type, value)].get("source") or "asset_import")
        try:
            if asset_type == "domain":
                domain = value.lower()
                root_domain = _guess_root_domain(domain)
                upsert_subdomain(
                    db=db,
                    project_id=project_id,
                    root_domain=root_domain,
                    subdomain=domain,
                    source=source,
                    ip_addresses=[],
                )
            elif asset_type == "ip":
                upsert_ip_address(
                    db=db,
                    project_id=project_id,
                    ip=value,
                    source=source,
                )
            elif asset_type == "url":
                normalized = _normalize_url(value)
                if normalized:
                    upsert_web_asset(
                        db=db,
                        project_id=project_id,
                        url=normalized,
                    )
        except Exception:
            logger.exception(
                "Failed to sync imported asset to scan tables: project=%s type=%s value=%s",
                project_id,
                asset_type,
                value,
            )


@router.post("/import", response_model=AssetImportResult)
def import_assets(
    payload: AssetImportRequest,
    project=Depends(get_project_dep),
    db: Session = Depends(get_db),
) -> AssetImportResult:
    raw_assets = [asset.model_dump() for asset in payload.assets]
    inserted, skipped, total = bulk_import_assets(
        db,
        project_id=project.id,
        assets=raw_assets,
    )
    _sync_assets_for_scan(db=db, project_id=project.id, assets=raw_assets)

    if inserted > 0:
        asset_types = sorted({_asset_type_value(asset.get("asset_type")) for asset in raw_assets})
        domain_values = [
            str(asset.get("value"))
            for asset in raw_assets
            if _asset_type_value(asset.get("asset_type")) == "domain"
        ]
        ip_values = [
            str(asset.get("value"))
            for asset in raw_assets
            if _asset_type_value(asset.get("asset_type")) == "ip"
        ]
        url_values = [
            _normalize_url(str(asset.get("value")))
            for asset in raw_assets
            if _asset_type_value(asset.get("asset_type")) == "url"
        ]
        event_data = {
            "source": "assets_import",
            "inserted": inserted,
            "skipped": skipped,
            "total": total,
            "asset_types": asset_types,
            "domain": domain_values[0] if domain_values else None,
            "domains": domain_values[:50],
            "ips": ip_values[:100],
            "urls": [url for url in url_values if url][:50],
        }
        try:
            event_handler.process_event.delay(
                project_id=str(project.id),
                event_type="asset_created",
                event_data=event_data,
            )
        except Exception:  # pragma: no cover - best-effort dispatch
            logger.exception(
                "Failed to enqueue asset_created event for project %s",
                project.id,
            )

    return AssetImportResult(inserted=inserted, skipped=skipped, total=total)


@router.get("", response_model=Page[AssetEntityOut])
def list_assets_endpoint(
    asset_type: AssetType | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    project=Depends(get_project_dep),
    db: Session = Depends(get_db),
) -> Page[AssetEntityOut]:
    total, items = list_assets(
        db, project_id=project.id, asset_type=asset_type, offset=offset, limit=limit
    )
    return Page(total=total, items=items)
