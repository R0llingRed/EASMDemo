"""Tests for domain validation pattern."""
import re

# Copy the pattern from worker/app/tasks/scan.py for standalone testing
DOMAIN_PATTERN = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


class TestDomainValidation:
    """Test domain validation."""

    def test_valid_domain(self):
        """Test valid domain patterns."""
        valid_domains = [
            "example.com",
            "sub.example.com",
            "a.b.c.example.com",
            "example-site.com",
            "123.com",
        ]
        for domain in valid_domains:
            assert DOMAIN_PATTERN.match(domain), f"{domain} should be valid"

    def test_invalid_domain(self):
        """Test invalid domain patterns."""
        invalid_domains = [
            "-example.com",
            "example-.com",
            ".example.com",
            "example..com",
            "",
        ]
        for domain in invalid_domains:
            assert not DOMAIN_PATTERN.match(domain), f"{domain} should be invalid"
