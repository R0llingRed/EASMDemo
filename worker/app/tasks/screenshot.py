"""Screenshot capture tasks."""
import logging
import os
from typing import Any, Dict
from uuid import UUID

from worker.app.celery_app import celery_app
from worker.app.tasks.dag_callback import notify_dag_node_completion
from worker.app.utils.scan_helpers import wait_for_project_rate_limit

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = os.environ.get("EASM_SCREENSHOT_DIR", "/app/data/screenshots")


@celery_app.task(bind=True, name="worker.app.tasks.screenshot.run_screenshot")
def run_screenshot(self, task_id: str):
    """Capture screenshots for web assets."""
    from server.app.crud import scan_task as crud_scan_task
    from server.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        task = crud_scan_task.get_scan_task(db, UUID(task_id))
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        if task.status in {"paused", "cancelled"}:
            logger.info("Task %s is %s, skip execution", task_id, task.status)
            return

        crud_scan_task.update_scan_task_status(db, task.id, "running")
        if not wait_for_project_rate_limit(
            db=db,
            project_id=task.project_id,
            task_config=task.config,
        ):
            raise RuntimeError("Rate limit wait timeout for project scan execution")
        result = _run_screenshot(db, task)
        crud_scan_task.update_scan_task_status(
            db, task.id, "completed", result_summary=result
        )
        notify_dag_node_completion(db=db, scan_task_id=task.id, success=True)
    except Exception as e:
        logger.exception(f"Task {task_id} failed")
        task_uuid = UUID(task_id)
        db.rollback()
        try:
            crud_scan_task.update_scan_task_status(
                db, task_uuid, "failed", error_message=str(e)
            )
        except Exception:
            logger.exception("Failed to persist failed status for task %s", task_id)
        notify_dag_node_completion(db=db, scan_task_id=task_uuid, success=False)
    finally:
        db.close()


def _run_screenshot(db, task) -> Dict[str, Any]:
    """Capture screenshots for web assets."""
    from server.app.crud.web_asset import list_web_assets, upsert_web_asset

    config = task.config or {}
    batch_size = config.get("batch_size", 100)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    assets = list_web_assets(db, task.project_id, is_alive=True, limit=batch_size)
    captured_count = 0

    for asset in assets:
        if asset.screenshot_path:
            continue

        screenshot_path = _capture_screenshot(asset.url, str(task.project_id))
        if screenshot_path:
            upsert_web_asset(
                db=db,
                project_id=task.project_id,
                url=asset.url,
                screenshot_path=screenshot_path,
            )
            captured_count += 1

    return {"assets_processed": len(assets), "captured": captured_count}


def _capture_screenshot(url: str, project_id: str) -> str:
    """Capture screenshot using gowitness or fallback."""
    import hashlib
    import shutil
    import subprocess

    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    filename = f"{project_id}_{url_hash}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    if shutil.which("gowitness"):
        try:
            subprocess.run(
                ["gowitness", "single", url, "-o", filepath, "--timeout", "15"],
                capture_output=True,
                timeout=30,
            )
            if os.path.exists(filepath):
                return f"/screenshots/{filename}"
        except Exception as e:
            logger.warning(f"gowitness failed for {url}: {e}")

    return ""
