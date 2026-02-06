"""Helpers for JavaScript endpoint extraction and API risk classification."""

import re
from urllib.parse import urljoin

# Extract <script src="..."> references.
SCRIPT_SRC_PATTERN = re.compile(
    r"<script[^>]*\bsrc=['\"]([^'\"]+)['\"][^>]*>\s*</script>",
    re.IGNORECASE,
)

# Extract inline <script>...</script> blocks (without src attribute).
INLINE_SCRIPT_PATTERN = re.compile(
    r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)

AXIOS_CALL_PATTERN = re.compile(
    r"axios\.(get|post|put|patch|delete)\(\s*['\"`]([^'\"`]+)['\"`]",
    re.IGNORECASE,
)

FETCH_CALL_PATTERN = re.compile(
    r"fetch\(\s*['\"`]([^'\"`]+)['\"`]\s*(?:,\s*\{(?P<options>[^}]*)\})?",
    re.IGNORECASE | re.DOTALL,
)

GENERIC_ENDPOINT_PATTERN = re.compile(
    r"['\"`](https?://[^'\"`\s]+|/(?:api|graphql|rest|v\d+)[^'\"`\s]*)['\"`]",
    re.IGNORECASE,
)

METHOD_PATTERN = re.compile(r"method\s*:\s*['\"`]([a-zA-Z]+)['\"`]", re.IGNORECASE)


def extract_scripts_from_html(html: str, page_url: str) -> list[dict]:
    """Extract external and inline script blocks from HTML."""
    scripts: list[dict] = []

    for match in SCRIPT_SRC_PATTERN.finditer(html):
        src = match.group(1).strip()
        if not src:
            continue
        scripts.append(
            {
                "script_type": "external",
                "script_url": urljoin(page_url, src),
                "content": None,
            }
        )

    for idx, match in enumerate(INLINE_SCRIPT_PATTERN.finditer(html)):
        content = match.group(1).strip()
        if not content:
            continue
        scripts.append(
            {
                "script_type": "inline",
                "script_url": f"{page_url}#inline-{idx}",
                "content": content,
            }
        )

    return scripts


def normalize_endpoint(raw_endpoint: str) -> str | None:
    """Normalize endpoint string and discard dynamic/invalid items."""
    endpoint = raw_endpoint.strip()
    if not endpoint:
        return None
    if "${" in endpoint or "{{" in endpoint:
        return None
    if endpoint.startswith("//"):
        return f"https:{endpoint}"
    if endpoint.startswith(("http://", "https://", "/")):
        return endpoint
    if endpoint.startswith("api/"):
        return f"/{endpoint}"
    return None


def _build_evidence(content: str, start: int, end: int, radius: int = 50) -> str:
    left = max(0, start - radius)
    right = min(len(content), end + radius)
    return content[left:right].replace("\n", " ").strip()


def extract_endpoints_from_js(content: str) -> list[dict]:
    """Extract potential API endpoints from JavaScript code."""
    findings: dict[tuple[str, str], dict] = {}

    for match in AXIOS_CALL_PATTERN.finditer(content):
        method = match.group(1).upper()
        endpoint = normalize_endpoint(match.group(2))
        if not endpoint:
            continue
        key = (method, endpoint)
        findings[key] = {
            "method": method,
            "endpoint": endpoint,
            "evidence": _build_evidence(content, match.start(), match.end()),
        }

    for match in FETCH_CALL_PATTERN.finditer(content):
        endpoint = normalize_endpoint(match.group(1))
        if not endpoint:
            continue
        options = match.group("options") or ""
        method_match = METHOD_PATTERN.search(options)
        method = method_match.group(1).upper() if method_match else "GET"
        key = (method, endpoint)
        findings[key] = {
            "method": method,
            "endpoint": endpoint,
            "evidence": _build_evidence(content, match.start(), match.end()),
        }

    for match in GENERIC_ENDPOINT_PATTERN.finditer(content):
        endpoint = normalize_endpoint(match.group(1))
        if not endpoint:
            continue
        key = ("GET", endpoint)
        findings.setdefault(
            key,
            {
                "method": "GET",
                "endpoint": endpoint,
                "evidence": _build_evidence(content, match.start(), match.end()),
            },
        )

    return sorted(findings.values(), key=lambda x: (x["endpoint"], x["method"]))


def classify_endpoint_risks(endpoint: str, method: str) -> list[dict]:
    """Classify endpoint risks with lightweight static rules."""
    method_upper = (method or "GET").upper()
    endpoint_lower = endpoint.lower()
    risks = []

    if endpoint_lower.startswith("http://"):
        risks.append(
            {
                "rule_name": "insecure_transport",
                "severity": "medium",
                "title": "Insecure API transport over HTTP",
                "description": "Endpoint uses HTTP and may be exposed to MITM.",
                "risk_tags": ["transport", "http"],
            }
        )

    if any(marker in endpoint_lower for marker in ("/admin", "/internal", "/debug", "/actuator")):
        risks.append(
            {
                "rule_name": "sensitive_api_surface",
                "severity": "high",
                "title": "Sensitive management endpoint exposed in frontend JS",
                "description": "Endpoint path indicates management/debug interfaces.",
                "risk_tags": ["exposure", "management"],
            }
        )

    if method_upper in {"POST", "PUT", "PATCH", "DELETE"} and any(
        marker in endpoint_lower for marker in ("/admin", "/internal", "/config", "/system")
    ):
        risks.append(
            {
                "rule_name": "mutation_on_sensitive_surface",
                "severity": "high",
                "title": "State-changing operation on sensitive endpoint",
                "description": "Mutating methods on sensitive API paths need strict auth controls.",
                "risk_tags": ["authz", "mutation"],
            }
        )

    if "/graphql" in endpoint_lower:
        risks.append(
            {
                "rule_name": "graphql_surface",
                "severity": "low",
                "title": "GraphQL endpoint exposed",
                "description": "GraphQL endpoints should enforce query depth and auth checks.",
                "risk_tags": ["graphql"],
            }
        )

    return risks
