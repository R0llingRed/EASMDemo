"""Xray web vulnerability scanning tasks."""
import json
import logging
import os
import re
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from worker.app.celery_app import celery_app

logger = logging.getLogger(__name__)

# Valid xray plugins
VALID_PLUGINS = {
    "xss", "sqldet", "cmd-injection", "dirscan", "path-traversal",
    "xxe", "upload", "brute-force", "jsonp", "ssrf", "baseline",
    "redirect", "crlf-injection", "xstream", "struts",
}

# Plugin name validation pattern
PLUGIN_PATTERN = re.compile(r"^[\w\-]+$")


@celery_app.task(bind=True, name="worker.app.tasks.xray_scan.run_xray_scan")
def run_xray_scan(self, task_id: str):
    """Run Xray web vulnerability scan."""
    from server.app.crud import scan_task as crud_scan_task
    from server.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        task = crud_scan_task.get_scan_task(db, UUID(task_id))
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        crud_scan_task.update_scan_task_status(db, task.id, "running")
        result = _run_xray_scan(db, task)
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


def _run_xray_scan(db: Session, task) -> Dict[str, Any]:
    """Execute Xray scan on web assets."""
    from server.app.crud.web_asset import list_web_assets

    config = task.config or {}
    batch_size = config.get("batch_size", 50)
    plugins = config.get("plugins", [])
    use_crawler = config.get("use_crawler", False)

    # Validate plugins
    plugins = _validate_plugins(plugins)

    assets = list_web_assets(db, task.project_id, is_alive=True, limit=batch_size)
    urls = [a.url for a in assets]

    if not urls:
        return {"urls_scanned": 0, "vulnerabilities_found": 0}

    vuln_count = 0
    for url in urls:
        results = _execute_xray(url, plugins, use_crawler)
        for result in results:
            _save_vulnerability(db, task.project_id, task.id, result)
            vuln_count += 1

    return {"urls_scanned": len(urls), "vulnerabilities_found": vuln_count}


def _validate_plugins(plugins: List[str]) -> List[str]:
    """Validate and sanitize plugin names."""
    valid_plugins = []
    for p in plugins:
        p_lower = p.strip().lower()
        if PLUGIN_PATTERN.match(p_lower) and p_lower in VALID_PLUGINS:
            valid_plugins.append(p_lower)
    return valid_plugins


def _execute_xray(
    url: str, plugins: List[str], use_crawler: bool
) -> List[Dict[str, Any]]:
    """Execute xray command and parse results."""
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("xray"):
        logger.warning("xray not found, skipping scan")
        return []

    results = []
    output_file = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            output_file = f.name

        cmd = ["xray", "webscan"]

        if use_crawler:
            cmd.extend(["--basic-crawler", url])
        else:
            cmd.extend(["--url", url])

        cmd.extend(["--json-output", output_file])

        if plugins:
            cmd.extend(["--plugins", ",".join(plugins)])

        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                content = f.read().strip()
                if content:
                    results = _parse_xray_output(content)

    except subprocess.TimeoutExpired:
        logger.warning(f"xray scan timed out for {url}")
    except Exception as e:
        logger.error(f"xray execution failed: {e}")
    finally:
        if output_file and os.path.exists(output_file):
            os.unlink(output_file)

    return results


def _parse_xray_output(content: str) -> List[Dict[str, Any]]:
    """Parse xray JSON output."""
    results = []
    try:
        # xray may output as array or newline-delimited JSON
        if content.startswith("["):
            results = json.loads(content)
        else:
            for line in content.split("\n"):
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse xray output: {e}")
    return results


def _save_vulnerability(
    db: Session, project_id: UUID, task_id: UUID, result: Dict[str, Any]
) -> None:
    """Save xray result as vulnerability."""
    from server.app.crud.vulnerability import upsert_vulnerability

    # Extract fields from xray output format
    plugin = result.get("plugin", "unknown")
    detail = result.get("detail", {})
    target = result.get("target", {})

    # Get URL from various possible locations
    target_url = (
        result.get("url")
        or detail.get("url")
        or target.get("url")
        or ""
    )

    upsert_vulnerability(
        db=db,
        project_id=project_id,
        target_url=target_url,
        template_id=f"xray-{plugin}",
        template_name=plugin,
        severity=_map_severity(result.get("severity", "medium")),
        vuln_type=plugin,
        title=detail.get("title") or f"Xray: {plugin}",
        description=detail.get("description"),
        matched_at=target_url,
        request=detail.get("request"),
        response=detail.get("response"),
        scan_task_id=task_id,
        raw_output=result,
    )


def _map_severity(severity: str) -> str:
    """Map xray severity to standard severity."""
    severity_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "info",
    }
    return severity_map.get(severity.lower(), "medium")
