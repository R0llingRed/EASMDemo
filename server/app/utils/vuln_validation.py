"""Vulnerability confidence scoring and validation."""
from typing import Dict, List


def calculate_confidence(
    scanner: str,
    has_evidence: bool = False,
    multi_source: bool = False,
    historical_hit: bool = False,
) -> int:
    """Calculate confidence score for a vulnerability.

    Returns score from 0-100.
    """
    base_scores = {
        "nuclei": 60,
        "xray": 65,
        "manual": 90,
        "unknown": 40,
    }

    score = base_scores.get(scanner.lower(), 40)

    # Adjustments
    if has_evidence:
        score += 15
    if multi_source:
        score += 20
    if historical_hit:
        score += 10

    return min(100, score)


def merge_sources(findings: List[Dict]) -> Dict:
    """Merge findings from multiple sources."""
    if not findings:
        return {}

    merged = findings[0].copy()
    sources = {merged.get("scanner", "unknown")}

    for f in findings[1:]:
        sources.add(f.get("scanner", "unknown"))
        # Keep higher severity
        if _severity_rank(f.get("severity")) > _severity_rank(merged.get("severity")):
            merged["severity"] = f["severity"]

    merged["sources"] = list(sources)
    merged["multi_source"] = len(sources) > 1

    return merged


def _severity_rank(severity: str) -> int:
    """Get numeric rank for severity."""
    ranks = {
        "critical": 5,
        "high": 4,
        "medium": 3,
        "low": 2,
        "info": 1,
    }
    return ranks.get(severity, 0)
