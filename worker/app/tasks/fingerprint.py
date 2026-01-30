"""Fingerprint identification tasks."""
import logging
from typing import Any, Dict, List
from uuid import UUID

from worker.app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="worker.app.tasks.fingerprint.run_fingerprint")
def run_fingerprint(self, task_id: str):
    """Run fingerprint identification for web assets."""
    from server.app.crud import scan_task as crud_scan_task
    from server.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        task = crud_scan_task.get_scan_task(db, UUID(task_id))
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        crud_scan_task.update_scan_task_status(db, task.id, "running")
        result = _run_fingerprint(db, task)
        crud_scan_task.update_scan_task_status(
            db, task.id, "completed", result_summary=result
        )
    except Exception as e:
        logger.exception(f"Task {task_id} failed")
        crud_scan_task.update_scan_task_status(
            db, UUID(task_id), "failed", error_message=str(e)
        )
    finally:
        db.close()


def _run_fingerprint(db, task) -> Dict[str, Any]:
    """Identify fingerprints for web assets."""
    from server.app.crud.web_asset import list_web_assets, upsert_web_asset

    config = task.config or {}
    batch_size = config.get("batch_size", 500)

    assets = list_web_assets(db, task.project_id, is_alive=True, limit=batch_size)
    identified_count = 0

    for asset in assets:
        fingerprints = _identify_fingerprints(asset)
        if fingerprints:
            upsert_web_asset(
                db=db,
                project_id=task.project_id,
                url=asset.url,
                fingerprints=fingerprints,
            )
            identified_count += 1

    return {"assets_scanned": len(assets), "identified": identified_count}


def _identify_fingerprints(asset) -> List[str]:
    """Identify fingerprints based on asset attributes."""
    fingerprints = []

    # Server-based fingerprints
    if asset.server:
        server_lower = asset.server.lower()
        if "nginx" in server_lower:
            fingerprints.append("Nginx")
        elif "apache" in server_lower:
            fingerprints.append("Apache")
        elif "iis" in server_lower:
            fingerprints.append("IIS")
        elif "tomcat" in server_lower:
            fingerprints.append("Tomcat")

    # Title-based fingerprints
    if asset.title:
        title_lower = asset.title.lower()
        _check_title_fingerprints(title_lower, fingerprints)

    return fingerprints


def _check_title_fingerprints(title: str, fingerprints: List[str]) -> None:
    """Check title for common fingerprints."""
    patterns = {
        "wordpress": "WordPress",
        "drupal": "Drupal",
        "joomla": "Joomla",
        "phpmyadmin": "phpMyAdmin",
        "weblogic": "WebLogic",
        "jenkins": "Jenkins",
        "gitlab": "GitLab",
        "grafana": "Grafana",
        "kibana": "Kibana",
        "zabbix": "Zabbix",
        "nagios": "Nagios",
        "confluence": "Confluence",
        "jira": "Jira",
    }
    for pattern, name in patterns.items():
        if pattern in title:
            fingerprints.append(name)
