"""Fingerprint loader module for loading FingerprintHub rules."""
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default path for fingerprint database
DEFAULT_FINGERPRINT_PATH = os.environ.get(
    "EASM_FINGERPRINT_DB",
    "/app/data/fingerprints/web_fingerprint_v4.json"
)

# Local development path
LOCAL_FINGERPRINT_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../../data/fingerprints/web_fingerprint_v4.json"
)

_fingerprint_cache: Optional[List[Dict[str, Any]]] = None


def load_fingerprints(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load fingerprints from JSON file.

    Args:
        path: Path to fingerprint JSON file. Uses default if not provided.

    Returns:
        List of fingerprint rules.
    """
    global _fingerprint_cache

    if _fingerprint_cache is not None:
        return _fingerprint_cache

    fp_path = path or DEFAULT_FINGERPRINT_PATH

    # Try local development path if default doesn't exist
    if not os.path.exists(fp_path):
        local_path = os.path.normpath(LOCAL_FINGERPRINT_PATH)
        if os.path.exists(local_path):
            fp_path = local_path

    if not os.path.exists(fp_path):
        logger.warning(f"Fingerprint database not found: {fp_path}")
        return []

    try:
        with open(fp_path, "r", encoding="utf-8") as f:
            fingerprints = json.load(f)

        logger.info(f"Loaded {len(fingerprints)} fingerprints from {fp_path}")
        _fingerprint_cache = fingerprints
        return fingerprints
    except Exception as e:
        logger.error(f"Failed to load fingerprints: {e}")
        return []


def clear_cache() -> None:
    """Clear the fingerprint cache."""
    global _fingerprint_cache
    _fingerprint_cache = None
