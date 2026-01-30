"""Scan task utilities."""
from typing import Any, Dict, Optional
from uuid import UUID

from server.app.utils.rate_limiter import get_rate_limiter


def get_rate_limit_config(project_config: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """Get rate limit configuration with defaults."""
    config = project_config or {}
    return {
        "max_requests_per_second": config.get("max_requests_per_second", 10),
        "max_concurrent_scans": config.get("max_concurrent_scans", 5),
    }


def check_rate_limit(project_id: UUID, config: Optional[Dict[str, Any]] = None) -> bool:
    """Check if scan is allowed under rate limit."""
    limiter = get_rate_limiter()
    rate_config = get_rate_limit_config(config)
    return limiter.is_allowed(
        identifier=f"scan:{project_id}",
        max_requests=rate_config["max_requests_per_second"],
        window_seconds=1,
    )


def wait_for_rate_limit(
    project_id: UUID,
    config: Optional[Dict[str, Any]] = None,
    max_wait: float = 10.0,
) -> bool:
    """Wait until rate limit allows, or timeout."""
    limiter = get_rate_limiter()
    rate_config = get_rate_limit_config(config)
    return limiter.wait_if_needed(
        identifier=f"scan:{project_id}",
        max_requests=rate_config["max_requests_per_second"],
        window_seconds=1,
        max_wait=max_wait,
    )
