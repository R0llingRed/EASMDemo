"""Tests for HTTP probe response parsing."""
import re


def _extract_title(body: str) -> str:
    """Extract title from HTML body."""
    title_match = re.search(r"<title>([^<]+)</title>", body, re.I)
    return title_match.group(1).strip() if title_match else None


class TestTitleExtraction:
    """Tests for HTML title extraction."""

    def test_simple_title(self):
        body = "<html><head><title>My Website</title></head></html>"
        assert _extract_title(body) == "My Website"

    def test_title_with_whitespace(self):
        body = "<html><head><title>  My Website  </title></head></html>"
        assert _extract_title(body) == "My Website"

    def test_no_title(self):
        body = "<html><head></head></html>"
        assert _extract_title(body) is None

    def test_case_insensitive(self):
        body = "<html><head><TITLE>My Website</TITLE></head></html>"
        assert _extract_title(body) == "My Website"

    def test_mixed_case(self):
        body = "<html><head><Title>My Website</Title></head></html>"
        assert _extract_title(body) == "My Website"

    def test_title_with_special_chars(self):
        body = "<html><head><title>Site - Dashboard | Admin</title></head></html>"
        assert _extract_title(body) == "Site - Dashboard | Admin"

    def test_empty_title(self):
        body = "<html><head><title></title></head></html>"
        # Empty title doesn't match regex pattern ([^<]+) which requires at least one char
        assert _extract_title(body) is None

    def test_multiline_title(self):
        body = "<html><head><title>My\nWebsite</title></head></html>"
        assert _extract_title(body) == "My\nWebsite"
