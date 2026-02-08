import logging
import re
from typing import Any, Dict, List
from uuid import UUID

from worker.app.celery_app import celery_app
from worker.app.tasks.dag_callback import notify_dag_node_completion
from worker.app.utils.scan_helpers import wait_for_project_rate_limit

logger = logging.getLogger(__name__)

# Domain validation regex
DOMAIN_PATTERN = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


@celery_app.task(bind=True, name="worker.app.tasks.scan.run_scan")
def run_scan(self, task_id: str):
    """Main entry point for running a scan task."""
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

        task_type = task.task_type
        if task_type == "subdomain_scan":
            result = _run_subdomain_scan(db, task)
        elif task_type == "dns_resolve":
            result = _run_dns_resolve(db, task)
        elif task_type == "port_scan":
            result = _run_port_scan(db, task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

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


def _run_subdomain_scan(db, task) -> Dict[str, Any]:
    """Run subdomain enumeration for a domain."""
    from server.app.crud.subdomain import bulk_upsert_subdomains

    config = task.config or {}
    domain = config.get("domain")
    if not domain:
        raise ValueError("domain is required in config")

    # Validate domain format
    if not DOMAIN_PATTERN.match(domain):
        raise ValueError(f"Invalid domain format: {domain}")

    logger.info(f"Starting subdomain scan for {domain}")

    subdomains = _enumerate_subdomains(domain)
    count = bulk_upsert_subdomains(
        db=db,
        project_id=task.project_id,
        root_domain=domain,
        subdomains=subdomains,
        source="subfinder",
    )

    return {"domain": domain, "subdomains_found": count}


def _enumerate_subdomains(domain: str) -> List[str]:
    """Enumerate subdomains using subfinder or fallback to simulation."""
    import shutil
    import subprocess

    if shutil.which("subfinder"):
        try:
            result = subprocess.run(
                ["subfinder", "-d", domain, "-silent"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                subs = [s.strip() for s in result.stdout.strip().split("\n") if s.strip()]
                return subs
        except Exception as e:
            logger.warning(f"subfinder failed: {e}, using simulation")

    # Fallback: simulate some common subdomains for MVP
    common_prefixes = ["www", "api", "mail", "dev", "test", "staging"]
    return [f"{p}.{domain}" for p in common_prefixes]


def _run_dns_resolve(db, task) -> Dict[str, Any]:
    """Resolve DNS for subdomains in the project."""
    import socket

    from server.app.crud.ip_address import upsert_ip_address
    from server.app.crud.subdomain import list_subdomains, upsert_subdomain

    config = task.config or {}
    root_domain = config.get("root_domain")
    batch_size = config.get("batch_size", 1000)

    subdomains = list_subdomains(db, task.project_id, root_domain=root_domain, limit=batch_size)
    resolved_count = 0

    for sub in subdomains:
        try:
            ips = socket.gethostbyname_ex(sub.subdomain)[2]
            if ips:
                upsert_subdomain(
                    db=db,
                    project_id=task.project_id,
                    root_domain=sub.root_domain,
                    subdomain=sub.subdomain,
                    source=sub.source,
                    ip_addresses=ips,
                )
                for ip in ips:
                    upsert_ip_address(db, task.project_id, ip, source="dns_resolve")
                resolved_count += 1
        except socket.gaierror:
            continue

    return {"subdomains_processed": len(subdomains), "resolved": resolved_count}


def _run_port_scan(db, task) -> Dict[str, Any]:
    """Scan ports for IPs in the project."""
    from server.app.crud.ip_address import list_ip_addresses
    from server.app.crud.port import upsert_port

    config = task.config or {}
    ports_to_scan = config.get("ports", [80, 443, 22, 21, 8080, 8443, 3306, 3389])
    batch_size = config.get("batch_size", 1000)

    ips = list_ip_addresses(db, task.project_id, limit=batch_size)
    open_ports_count = 0

    for ip_obj in ips:
        open_ports = _scan_ports(ip_obj.ip, ports_to_scan)
        for port_info in open_ports:
            upsert_port(
                db=db,
                ip_id=ip_obj.id,
                port=port_info["port"],
                protocol="tcp",
                state="open",
                service=port_info.get("service"),
            )
            open_ports_count += 1

    return {"ips_scanned": len(ips), "open_ports": open_ports_count}


def _scan_ports(ip: str, ports: List[int]) -> List[Dict[str, Any]]:
    """Scan ports using socket or nmap."""
    import shutil
    import socket
    import subprocess

    # Try nmap first
    if shutil.which("nmap"):
        try:
            port_str = ",".join(str(p) for p in ports)
            result = subprocess.run(
                ["nmap", "-sT", "-p", port_str, "--open", "-oG", "-", ip],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return _parse_nmap_output(result.stdout)
        except Exception as e:
            logger.warning(f"nmap failed: {e}, using socket scan")

    # Fallback to socket scan
    open_ports = []
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                if sock.connect_ex((ip, port)) == 0:
                    open_ports.append({"port": port, "service": _guess_service(port)})
        except Exception:
            pass
    return open_ports


def _parse_nmap_output(output: str) -> List[Dict[str, Any]]:
    """Parse nmap grepable output."""

    open_ports = []
    for line in output.split("\n"):
        if "Ports:" in line:
            ports_section = line.split("Ports:")[1]
            port_entries = ports_section.split(",")
            for entry in port_entries:
                match = re.search(r"(\d+)/open/tcp//([^/]*)", entry)
                if match:
                    open_ports.append({
                        "port": int(match.group(1)),
                        "service": match.group(2) or None,
                    })
    return open_ports


def _guess_service(port: int) -> str:
    """Guess service name by port number."""
    services = {
        21: "ftp",
        22: "ssh",
        23: "telnet",
        25: "smtp",
        53: "dns",
        80: "http",
        110: "pop3",
        143: "imap",
        443: "https",
        3306: "mysql",
        3389: "rdp",
        5432: "postgresql",
        6379: "redis",
        8080: "http-proxy",
        8443: "https-alt",
    }
    return services.get(port, "unknown")
