"""Fingerprint identification tasks."""
import hashlib
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from worker.app.celery_app import celery_app
from worker.app.fingerprint import FingerprintEngine, load_fingerprints

logger = logging.getLogger(__name__)

# Global engine instance (lazy loaded)
_engine: Optional[FingerprintEngine] = None


def get_engine() -> FingerprintEngine:
    """Get or create the fingerprint engine."""
    global _engine
    if _engine is None:
        fingerprints = load_fingerprints()
        _engine = FingerprintEngine(fingerprints)
    return _engine


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
    use_engine = config.get("use_fingerprinthub", True)

    assets = list_web_assets(db, task.project_id, is_alive=True, limit=batch_size)
    identified_count = 0

    engine = get_engine() if use_engine else None

    for asset in assets:
        fingerprints = _identify_fingerprints_for_asset(asset, engine)
        if fingerprints:
            upsert_web_asset(
                db=db,
                project_id=task.project_id,
                url=asset.url,
                fingerprints=fingerprints,
            )
            identified_count += 1

    return {"assets_scanned": len(assets), "identified": identified_count}


def _identify_fingerprints_for_asset(
    asset, engine: Optional[FingerprintEngine]
) -> List[str]:
    """Identify fingerprints for a single asset."""
    fingerprints = []

    # Always run basic fingerprinting
    fingerprints.extend(_identify_fingerprints_basic(asset))

    # Use FingerprintHub engine if available
    if engine:
        try:
            body, headers, favicon_hash = _fetch_response(asset.url)
            results = engine.match(body=body, headers=headers, favicon_hash=favicon_hash)
            for r in results:
                if r.name and r.name not in fingerprints:
                    fingerprints.append(r.name)
        except Exception as e:
            logger.debug(f"Engine matching failed for {asset.url}: {e}")

    return fingerprints


def _identify_fingerprints(asset) -> List[str]:
    """Identify fingerprints based on asset attributes (legacy)."""
    return _identify_fingerprints_basic(asset)


def _identify_fingerprints_basic(asset) -> List[str]:
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


def _fetch_response(url: str) -> tuple:
    """Fetch URL and return body, headers, and favicon hash."""
    import ssl
    import urllib.request

    body = ""
    headers = {}
    favicon_hash = None

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            url, headers={"User-Agent": "EASM-Scanner/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            body = resp.read(65536).decode("utf-8", errors="ignore")
            headers = dict(resp.headers)

            # Try to fetch favicon
            favicon_hash = _fetch_favicon_hash(url, body, ctx)
    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")

    return body, headers, favicon_hash


def _fetch_favicon_hash(url: str, body: str, ctx) -> Optional[str]:
    """Extract and hash favicon from page."""
    import re
    import urllib.request
    from urllib.parse import urljoin

    # Try to find favicon link in HTML
    favicon_url = None
    match = re.search(
        r'<link[^>]+rel=["\'](?:shortcut )?icon["\'][^>]+href=["\']([^"\']+)["\']',
        body,
        re.I,
    )
    if match:
        favicon_url = urljoin(url, match.group(1))
    else:
        # Default favicon path
        favicon_url = urljoin(url, "/favicon.ico")

    try:
        req = urllib.request.Request(
            favicon_url, headers={"User-Agent": "EASM-Scanner/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            favicon_data = resp.read(32768)
            if favicon_data:
                return hashlib.md5(favicon_data).hexdigest()
    except Exception:
        pass

    return None
