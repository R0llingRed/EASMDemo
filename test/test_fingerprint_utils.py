"""Tests for fingerprint utilities."""
from server.app.utils.fingerprint import (
    compute_ip_fingerprint,
    compute_subdomain_fingerprint,
    compute_url_fingerprint,
    normalize_url,
)


class TestNormalizeUrl:
    """Tests for URL normalization."""

    def test_basic_url(self):
        assert normalize_url("http://example.com") == "http://example.com/"

    def test_trailing_slash(self):
        assert normalize_url("http://example.com/") == "http://example.com/"

    def test_path(self):
        assert normalize_url("http://example.com/path") == "http://example.com/path"

    def test_default_http_port(self):
        assert normalize_url("http://example.com:80/") == "http://example.com/"

    def test_default_https_port(self):
        assert normalize_url("https://example.com:443/") == "https://example.com/"

    def test_non_default_port(self):
        assert normalize_url("http://example.com:8080/") == "http://example.com:8080/"

    def test_case_insensitive(self):
        assert normalize_url("HTTP://EXAMPLE.COM/") == "http://example.com/"


class TestFingerprintComputation:
    """Tests for fingerprint hash computation."""

    def test_subdomain_fingerprint_consistent(self):
        fp1 = compute_subdomain_fingerprint("proj1", "sub.example.com")
        fp2 = compute_subdomain_fingerprint("proj1", "sub.example.com")
        assert fp1 == fp2

    def test_subdomain_fingerprint_different_projects(self):
        fp1 = compute_subdomain_fingerprint("proj1", "sub.example.com")
        fp2 = compute_subdomain_fingerprint("proj2", "sub.example.com")
        assert fp1 != fp2

    def test_subdomain_fingerprint_case_insensitive(self):
        fp1 = compute_subdomain_fingerprint("proj1", "SUB.EXAMPLE.COM")
        fp2 = compute_subdomain_fingerprint("proj1", "sub.example.com")
        assert fp1 == fp2

    def test_ip_fingerprint_consistent(self):
        fp1 = compute_ip_fingerprint("proj1", "192.168.1.1")
        fp2 = compute_ip_fingerprint("proj1", "192.168.1.1")
        assert fp1 == fp2

    def test_ip_fingerprint_different_ips(self):
        fp1 = compute_ip_fingerprint("proj1", "192.168.1.1")
        fp2 = compute_ip_fingerprint("proj1", "192.168.1.2")
        assert fp1 != fp2

    def test_url_fingerprint_consistent(self):
        fp1 = compute_url_fingerprint("proj1", "http://example.com/path")
        fp2 = compute_url_fingerprint("proj1", "http://example.com/path")
        assert fp1 == fp2

    def test_url_fingerprint_normalized(self):
        fp1 = compute_url_fingerprint("proj1", "http://example.com:80/path")
        fp2 = compute_url_fingerprint("proj1", "http://example.com/path")
        assert fp1 == fp2

    def test_fingerprint_length(self):
        fp = compute_subdomain_fingerprint("proj1", "sub.example.com")
        assert len(fp) == 32
