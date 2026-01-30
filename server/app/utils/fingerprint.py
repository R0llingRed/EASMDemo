"""Asset fingerprint utilities for deduplication."""
import hashlib
from urllib.parse import urlparse


def compute_subdomain_fingerprint(project_id: str, subdomain: str) -> str:
    """Compute fingerprint hash for subdomain."""
    normalized = subdomain.lower().strip()
    data = f"{project_id}:subdomain:{normalized}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def compute_ip_fingerprint(project_id: str, ip: str) -> str:
    """Compute fingerprint hash for IP address."""
    normalized = ip.strip()
    data = f"{project_id}:ip:{normalized}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def compute_url_fingerprint(project_id: str, url: str) -> str:
    """Compute fingerprint hash for URL."""
    normalized = normalize_url(url)
    data = f"{project_id}:url:{normalized}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def normalize_url(url: str) -> str:
    """Normalize URL for consistent fingerprinting."""
    parsed = urlparse(url.lower().strip())
    # Reconstruct without trailing slash and default ports
    scheme = parsed.scheme or "http"
    host = parsed.netloc or parsed.path.split("/")[0]
    path = parsed.path.rstrip("/") or "/"

    # Remove default ports
    if host.endswith(":80") and scheme == "http":
        host = host[:-3]
    elif host.endswith(":443") and scheme == "https":
        host = host[:-4]

    return f"{scheme}://{host}{path}"


def compute_vuln_fingerprint(
    project_id: str,
    target_url: str,
    template_id: str,
) -> str:
    """Compute fingerprint hash for vulnerability."""
    normalized_url = normalize_url(target_url) if target_url else ""
    data = f"{project_id}:vuln:{normalized_url}:{template_id}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]
