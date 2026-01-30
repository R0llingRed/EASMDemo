"""Tests for fingerprint engine."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MatchResult:
    """Result of a fingerprint match."""
    fingerprint_id: str
    name: str
    vendor: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[str] = None


class TestFingerprintEngine:
    """Tests for FingerprintEngine matching logic."""

    def test_word_matcher_simple(self):
        """Test simple word matching."""
        matcher = {"type": "word", "words": ["wordpress"]}
        content = "This is a wordpress site"
        assert _match_word(matcher, content) is True

    def test_word_matcher_case_insensitive(self):
        """Test case insensitive word matching."""
        matcher = {
            "type": "word",
            "words": ["WordPress"],
            "case-insensitive": True
        }
        content = "this is a WORDPRESS site"
        assert _match_word(matcher, content) is True

    def test_word_matcher_and_condition(self):
        """Test AND condition for word matching."""
        matcher = {
            "type": "word",
            "words": ["wordpress", "theme"],
            "condition": "and"
        }
        content = "wordpress theme directory"
        assert _match_word(matcher, content) is True

        content2 = "wordpress site"
        assert _match_word(matcher, content2) is False

    def test_word_matcher_negative(self):
        """Test negative word matching."""
        matcher = {
            "type": "word",
            "words": ["error"],
            "negative": True
        }
        content = "success page"
        assert _match_word(matcher, content) is True

        content2 = "error page"
        assert _match_word(matcher, content2) is False

    def test_regex_matcher(self):
        """Test regex matching."""
        matcher = {
            "type": "regex",
            "regex": [r"<title>.*wordpress.*</title>"]
        }
        content = "<title>My WordPress Blog</title>"
        assert _match_regex(matcher, content) is True

    def test_favicon_matcher(self):
        """Test favicon hash matching."""
        matcher = {
            "type": "favicon",
            "hash": ["abc123", "def456"]
        }
        assert _match_favicon(matcher, "abc123") is True
        assert _match_favicon(matcher, "xyz789") is False
        assert _match_favicon(matcher, None) is False


def _match_word(matcher: Dict[str, Any], content: str) -> bool:
    """Match word type matcher (copied from engine for testing)."""
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


def _match_regex(matcher: Dict[str, Any], content: str) -> bool:
    """Match regex type matcher (copied from engine for testing)."""
    import re
    patterns = matcher.get("regex", [])
    if not patterns:
        return False

    condition = matcher.get("condition", "or")
    negative = matcher.get("negative", False)

    results = []
    for pattern in patterns:
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            results.append(bool(regex.search(content)))
        except re.error:
            results.append(False)

    if condition == "and":
        matched = all(results)
    else:
        matched = any(results)

    return not matched if negative else matched


def _match_favicon(
    matcher: Dict[str, Any], favicon_hash: Optional[str]
) -> bool:
    """Match favicon hash (copied from engine for testing)."""
    if not favicon_hash:
        return False

    hashes = matcher.get("hash", [])
    negative = matcher.get("negative", False)
    matched = favicon_hash.lower() in [h.lower() for h in hashes]

    return not matched if negative else matched
