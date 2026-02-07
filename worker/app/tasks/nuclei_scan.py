"""Nuclei vulnerability scanning tasks."""
import json
import logging
import os
import re
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from worker.app.celery_app import celery_app
from worker.app.tasks.dag_callback import notify_dag_node_completion
from worker.app.utils.scan_helpers import wait_for_project_rate_limit

logger = logging.getLogger(__name__)

# Valid severity levels for nuclei
VALID_SEVERITIES = {"info", "low", "medium", "high", "critical"}

# Template path validation pattern (alphanumeric, dash, underscore, slash, dot)
TEMPLATE_PATTERN = re.compile(r"^[\w\-./]+$")


@celery_app.task(bind=True, name="worker.app.tasks.nuclei_scan.run_nuclei_scan")
def run_nuclei_scan(self, task_id: str):
    """Run Nuclei vulnerability scan."""
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
        result = _run_nuclei_scan(db, task)
        crud_scan_task.update_scan_task_status(
            db, task.id, "completed", result_summary=result
        )
        notify_dag_node_completion(db=db, scan_task_id=task.id, success=True)
    except Exception as e:
        logger.exception(f"Task {task_id} failed")
        task_uuid = UUID(task_id)
        crud_scan_task.update_scan_task_status(
            db, task_uuid, "failed", error_message=str(e)
        )
        notify_dag_node_completion(db=db, scan_task_id=task_uuid, success=False)
    finally:
        db.close()


def _run_nuclei_scan(db: Session, task) -> Dict[str, Any]:
    """Execute Nuclei scan on web assets."""
    from server.app.crud.web_asset import list_web_assets

    config = task.config or {}
    batch_size = config.get("batch_size", 100)
    severity = config.get("severity", "medium,high,critical")
    templates = config.get("templates", [])

    # Validate severity input
    severity = _validate_severity(severity)
    # Validate templates input
    templates = _validate_templates(templates)

    assets = list_web_assets(db, task.project_id, is_alive=True, limit=batch_size)
    urls = [a.url for a in assets]

    if not urls:
        return {"urls_scanned": 0, "vulnerabilities_found": 0}

    results = _execute_nuclei(urls, severity, templates)
    vuln_count = 0

    for result in results:
        _save_vulnerability(db, task.project_id, task.id, result)
        vuln_count += 1

    return {"urls_scanned": len(urls), "vulnerabilities_found": vuln_count}


def _validate_severity(severity: str) -> str:
    """Validate and sanitize severity input."""
    parts = [s.strip().lower() for s in severity.split(",")]
    valid_parts = [p for p in parts if p in VALID_SEVERITIES]
    if not valid_parts:
        return "medium,high,critical"
    return ",".join(valid_parts)


def _validate_templates(templates: List[str]) -> List[str]:
    """Validate and sanitize template paths."""
    valid_templates = []
    for t in templates:
        if TEMPLATE_PATTERN.match(t) and ".." not in t:
            valid_templates.append(t)
    return valid_templates


def _execute_nuclei(
    urls: List[str], severity: str, templates: List[str]
) -> List[Dict[str, Any]]:
    """Execute nuclei command and parse results."""
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("nuclei"):
        logger.warning("nuclei not found, skipping scan")
        return []

    results = []
    targets_file = None

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("\n".join(urls))
            targets_file = f.name

        cmd = [
            "nuclei",
            "-l", targets_file,
            "-severity", severity,
            "-json",
            "-silent",
        ]

        if templates:
            cmd.extend(["-t", ",".join(templates)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )

        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    except subprocess.TimeoutExpired:
        logger.warning("nuclei scan timed out")
    except Exception as e:
        logger.error(f"nuclei execution failed: {e}")
    finally:
        if targets_file and os.path.exists(targets_file):
            os.unlink(targets_file)

    return results


def _save_vulnerability(db, project_id, task_id, result: Dict[str, Any]) -> None:
    """Save nuclei result as vulnerability."""
    from server.app.crud.vulnerability import upsert_vulnerability

    info = result.get("info", {})

    upsert_vulnerability(
        db=db,
        project_id=project_id,
        target_url=result.get("matched-at", result.get("host", "")),
        template_id=result.get("template-id", "unknown"),
        template_name=result.get("template", info.get("name")),
        severity=_map_severity(info.get("severity", "info")),
        vuln_type=result.get("type"),
        title=info.get("name"),
        description=info.get("description"),
        reference=info.get("reference", []),
        tags=info.get("tags", []),
        matched_at=result.get("matched-at"),
        matcher_name=result.get("matcher-name"),
        extracted_results=result.get("extracted-results", []),
        curl_command=result.get("curl-command"),
        request=result.get("request"),
        response=result.get("response"),
        scan_task_id=task_id,
        raw_output=result,
    )


def _map_severity(severity: str) -> str:
    """Map nuclei severity to standard severity."""
    severity_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "info",
        "unknown": "info",
    }
    return severity_map.get(severity.lower(), "info")
