"""Fingerprint matching engine."""
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of a fingerprint match."""
    fingerprint_id: str
    name: str
    vendor: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[str] = None


class FingerprintEngine:
    """Engine for matching web fingerprints."""

    def __init__(self, fingerprints: List[Dict[str, Any]]):
        """Initialize the engine with fingerprint rules."""
        self.fingerprints = fingerprints
        self._compiled_regex: Dict[str, re.Pattern] = {}
        logger.info(f"FingerprintEngine initialized with {len(fingerprints)} rules")

    def match(
        self,
        body: str = "",
        headers: Optional[Dict[str, str]] = None,
        favicon_hash: Optional[str] = None,
    ) -> List[MatchResult]:
        """Match response against all fingerprints."""
        results = []
        headers = headers or {}
        header_str = self._headers_to_string(headers)

        for fp in self.fingerprints:
            if self._match_fingerprint(fp, body, header_str, favicon_hash):
                result = self._create_result(fp)
                results.append(result)

        return results

    def _match_fingerprint(
        self,
        fp: Dict[str, Any],
        body: str,
        header_str: str,
        favicon_hash: Optional[str],
    ) -> bool:
        """Check if a single fingerprint matches."""
        http_probes = fp.get("http", [])
        if not http_probes:
            return False

        for probe in http_probes:
            matchers = probe.get("matchers", [])
            if not matchers:
                continue

            for matcher in matchers:
                if self._match_single_matcher(matcher, body, header_str, favicon_hash):
                    return True

        return False

    def _match_single_matcher(
        self,
        matcher: Dict[str, Any],
        body: str,
        header_str: str,
        favicon_hash: Optional[str],
    ) -> bool:
        """Match a single matcher against response."""
        matcher_type = matcher.get("type", "word")
        part = matcher.get("part", "body")
        content = header_str if part == "header" else body

        if matcher_type == "word":
            return self._match_word(matcher, content)
        elif matcher_type == "regex":
            return self._match_regex(matcher, content)
        elif matcher_type == "favicon":
            return self._match_favicon(matcher, favicon_hash)

        return False

    def _match_word(self, matcher: Dict[str, Any], content: str) -> bool:
        """Match word type matcher."""
        words = matcher.get("words", [])
        if not words:
            return False

        case_insensitive = matcher.get("case-insensitive", False)
        condition = matcher.get("condition", "or")
        negative = matcher.get("negative", False)

        if case_insensitive:
            content = content.lower()
            words = [w.lower() for w in words]

        if condition == "and":
            matched = all(w in content for w in words)
        else:
            matched = any(w in content for w in words)

        return not matched if negative else matched

    def _match_regex(self, matcher: Dict[str, Any], content: str) -> bool:
        """Match regex type matcher."""
        patterns = matcher.get("regex", [])
        if not patterns:
            return False

        condition = matcher.get("condition", "or")
        negative = matcher.get("negative", False)

        results = []
        for pattern in patterns:
            try:
                if pattern not in self._compiled_regex:
                    self._compiled_regex[pattern] = re.compile(pattern, re.IGNORECASE)
                regex = self._compiled_regex[pattern]
                results.append(bool(regex.search(content)))
            except re.error:
                logger.debug(f"Invalid regex pattern: {pattern}")
                results.append(False)

        if condition == "and":
            matched = all(results)
        else:
            matched = any(results)

        return not matched if negative else matched

    def _match_favicon(
        self, matcher: Dict[str, Any], favicon_hash: Optional[str]
    ) -> bool:
        """Match favicon hash."""
        if not favicon_hash:
            return False

        hashes = matcher.get("hash", [])
        negative = matcher.get("negative", False)
        matched = favicon_hash.lower() in [h.lower() for h in hashes]

        return not matched if negative else matched

    def _headers_to_string(self, headers: Dict[str, str]) -> str:
        """Convert headers dict to string for matching."""
        lines = [f"{k}: {v}" for k, v in headers.items()]
        return "\n".join(lines)

    def _create_result(self, fp: Dict[str, Any]) -> MatchResult:
        """Create MatchResult from fingerprint."""
        info = fp.get("info", {})
        metadata = info.get("metadata", {})

        return MatchResult(
            fingerprint_id=fp.get("id", "unknown"),
            name=info.get("name", fp.get("id", "unknown")),
            vendor=metadata.get("vendor"),
            product=metadata.get("product"),
            version=metadata.get("version"),
            tags=info.get("tags"),
        )
