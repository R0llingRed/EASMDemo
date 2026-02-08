"""HTTP probe and web asset discovery tasks."""
import logging
from typing import Any, Dict
from uuid import UUID

from shared.config import settings
from worker.app.celery_app import celery_app
from worker.app.tasks.dag_callback import notify_dag_node_completion
from worker.app.utils.scan_helpers import wait_for_project_rate_limit
from worker.app.utils.tls import create_ssl_context

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="worker.app.tasks.http_probe.run_http_probe")
def run_http_probe(self, task_id: str):
    """Run HTTP probe for ports in the project."""
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
        result = _run_http_probe(db, task)
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


def _run_http_probe(db, task) -> Dict[str, Any]:
    """Probe HTTP services for open ports."""
    from server.app.crud.ip_address import list_ip_addresses
    from server.app.crud.port import list_ports_by_ip
    from server.app.crud.web_asset import upsert_web_asset

    config = task.config or {}
    batch_size = config.get("batch_size", 500)
    verify_tls = settings.scan_verify_tls and not bool(config.get("insecure", False))

    ips = list_ip_addresses(db, task.project_id, limit=batch_size)
    probed_count = 0
    alive_count = 0

    for ip_obj in ips:
        ports = list_ports_by_ip(db, ip_obj.id, limit=100)
        http_ports = [
            p for p in ports
            if p.port in (80, 443, 8080, 8443) or p.service in ("http", "https")
        ]

        for port in http_ports:
            scheme = "https" if port.port in (443, 8443) else "http"
            url = f"{scheme}://{ip_obj.ip}:{port.port}"

            result = _probe_url(url, verify_tls=verify_tls)
            if result:
                upsert_web_asset(
                    db=db,
                    project_id=task.project_id,
                    url=url,
                    ip_id=ip_obj.id,
                    port_id=port.id,
                    **result,
                )
                if result.get("is_alive"):
                    alive_count += 1
            probed_count += 1

    return {"urls_probed": probed_count, "alive": alive_count}


def _probe_url(url: str, verify_tls: bool = True) -> Dict[str, Any]:
    """Probe a single URL using httpx or requests."""
    import shutil

    # Try httpx CLI first
    if shutil.which("httpx"):
        return _probe_with_httpx(url, verify_tls=verify_tls)

    # Fallback to Python requests
    return _probe_with_requests(url, verify_tls=verify_tls)


def _probe_with_httpx(url: str, verify_tls: bool = True) -> Dict[str, Any]:
    """Probe URL using httpx CLI."""
    import json
    import subprocess

    try:
        command = ["httpx", "-u", url, "-json", "-silent", "-timeout", "10"]
        if not verify_tls:
            command.append("-insecure")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            return {
                "title": data.get("title"),
                "status_code": data.get("status_code"),
                "content_length": data.get("content_length"),
                "content_type": data.get("content_type"),
                "server": data.get("webserver"),
                "technologies": data.get("tech", []),
                "is_alive": True,
            }
    except Exception as e:
        logger.warning(f"httpx probe failed for {url}: {e}")

    return {"is_alive": False}


def _probe_with_requests(url: str, verify_tls: bool = True) -> Dict[str, Any]:
    """Probe URL using Python urllib."""
    import re
    import urllib.request

    try:
        ctx = create_ssl_context(verify_tls=verify_tls)

        req = urllib.request.Request(url, headers={"User-Agent": "EASM-Scanner/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            body = resp.read(8192).decode("utf-8", errors="ignore")
            title_match = re.search(r"<title>([^<]+)</title>", body, re.I)

            return {
                "title": title_match.group(1).strip() if title_match else None,
                "status_code": resp.status,
                "content_length": int(resp.headers.get("Content-Length", 0)),
                "content_type": resp.headers.get("Content-Type"),
                "server": resp.headers.get("Server"),
                "is_alive": True,
            }
    except Exception as e:
        logger.debug(f"Request probe failed for {url}: {e}")

    return {"is_alive": False}
