"""JS and API deep discovery tasks."""

import hashlib
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from uuid import UUID

from shared.config import settings
from worker.app.celery_app import celery_app
from worker.app.tasks.dag_callback import notify_dag_node_completion
from worker.app.utils.js_api_parser import (
    classify_endpoint_risks,
    extract_endpoints_from_js,
    extract_scripts_from_html,
)
from worker.app.utils.scan_helpers import wait_for_project_rate_limit
from worker.app.utils.tls import create_ssl_context

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="worker.app.tasks.js_api_discovery.run_js_api_discovery")
def run_js_api_discovery(self, task_id: str):
    """Run JS deep analysis and API endpoint extraction."""
    from server.app.crud import scan_task as crud_scan_task
    from server.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        task = crud_scan_task.get_scan_task(db, UUID(task_id))
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        crud_scan_task.update_scan_task_status(db, task.id, "running")
        if not wait_for_project_rate_limit(
            db=db,
            project_id=task.project_id,
            task_config=task.config,
        ):
            raise RuntimeError("Rate limit wait timeout for project scan execution")
        result = _run_js_api_discovery(db, task)
        crud_scan_task.update_scan_task_status(
            db, task.id, "completed", result_summary=result
        )
        notify_dag_node_completion(db=db, scan_task_id=task.id, success=True)
    except Exception as exc:
        logger.exception(f"Task {task_id} failed")
        task_uuid = UUID(task_id)
        crud_scan_task.update_scan_task_status(
            db, task_uuid, "failed", error_message=str(exc)
        )
        notify_dag_node_completion(db=db, scan_task_id=task_uuid, success=False)
    finally:
        db.close()


def _run_js_api_discovery(db, task) -> Dict[str, Any]:
    """Discover JS assets, endpoints and API risks from project web assets."""
    from server.app.crud import api_endpoint as crud_api_endpoint
    from server.app.crud import api_risk_finding as crud_api_risk
    from server.app.crud import js_asset as crud_js_asset
    from server.app.crud.web_asset import list_web_assets

    config = task.config or {}
    batch_size = int(config.get("batch_size", 100))
    max_scripts_per_page = int(config.get("max_scripts_per_page", 20))
    max_script_size = int(config.get("max_script_size", 512000))
    verify_tls = settings.scan_verify_tls and not bool(config.get("insecure", False))

    assets = list_web_assets(db, task.project_id, is_alive=True, limit=batch_size)
    script_keys: set[tuple[str, str]] = set()
    endpoint_keys: set[tuple[str, str]] = set()
    risk_keys: set[tuple[str, str]] = set()

    for asset in assets:
        html = _fetch_text(asset.url, verify_tls=verify_tls, max_size=max_script_size)
        if not html:
            continue

        scripts = extract_scripts_from_html(html, asset.url)
        for script in scripts[:max_scripts_per_page]:
            script_content = script.get("content")
            if script.get("script_type") == "external":
                script_content = _fetch_text(
                    script["script_url"],
                    verify_tls=verify_tls,
                    max_size=max_script_size,
                )
            if not script_content:
                continue

            content_hash = hashlib.sha256(script_content.encode("utf-8")).hexdigest()
            js_asset = crud_js_asset.upsert_js_asset(
                db=db,
                project_id=task.project_id,
                web_asset_id=asset.id,
                script_url=script["script_url"],
                script_type=script["script_type"],
                content_hash=content_hash,
                source_url=asset.url,
                scan_metadata={"content_length": len(script_content)},
            )
            script_keys.add((script["script_url"], content_hash))

            endpoints = extract_endpoints_from_js(script_content)
            for endpoint_result in endpoints:
                method = endpoint_result["method"]
                endpoint = endpoint_result["endpoint"]
                endpoint_record = crud_api_endpoint.upsert_api_endpoint(
                    db=db,
                    project_id=task.project_id,
                    js_asset_id=js_asset.id,
                    endpoint=endpoint,
                    method=method,
                    host=_extract_host(endpoint),
                    evidence={
                        "script_url": script["script_url"],
                        "source_url": asset.url,
                        "snippet": endpoint_result.get("evidence"),
                    },
                )
                endpoint_keys.add((method, endpoint))

                for risk in classify_endpoint_risks(endpoint, method):
                    crud_api_risk.create_or_update_api_risk_finding(
                        db=db,
                        project_id=task.project_id,
                        endpoint_id=endpoint_record.id,
                        rule_name=risk["rule_name"],
                        severity=risk["severity"],
                        title=risk["title"],
                        description=risk["description"],
                        evidence={
                            "endpoint": endpoint,
                            "method": method,
                            "script_url": script["script_url"],
                            "risk_tags": risk.get("risk_tags", []),
                        },
                    )
                    risk_keys.add((str(endpoint_record.id), risk["rule_name"]))

    return {
        "pages_scanned": len(assets),
        "scripts_discovered": len(script_keys),
        "api_endpoints_discovered": len(endpoint_keys),
        "api_risks_flagged": len(risk_keys),
    }


def _fetch_text(url: str, verify_tls: bool, max_size: int = 512000) -> Optional[str]:
    """Fetch text response from URL with size guard."""
    import urllib.request

    try:
        context = create_ssl_context(verify_tls=verify_tls)
        req = urllib.request.Request(url, headers={"User-Agent": "EASM-JS-Analyzer/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=context) as resp:
            data = resp.read(max_size + 1)
            if len(data) > max_size:
                data = data[:max_size]
            return data.decode("utf-8", errors="ignore")
    except Exception as exc:
        logger.debug(f"Failed to fetch {url}: {exc}")
        return None


def _extract_host(endpoint: str) -> Optional[str]:
    """Extract host from absolute endpoint URL."""
    if not endpoint.startswith(("http://", "https://")):
        return None
    parsed = urlparse(endpoint)
    return parsed.hostname
