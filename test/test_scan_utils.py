"""Tests for scan filter and vulnerability validation."""
from server.app.utils.scan_filter import ScanFilter
from server.app.utils.vuln_validation import calculate_confidence, merge_sources


class TestScanFilter:
    """Tests for scan target filtering."""

    def test_no_rules_allows_all(self):
        f = ScanFilter()
        assert f.is_allowed("example.com")

    def test_blacklist_blocks(self):
        f = ScanFilter(blacklist=["*.gov", "*.mil"])
        assert not f.is_allowed("test.gov")
        assert f.is_allowed("example.com")

    def test_whitelist_only_allows_matching(self):
        f = ScanFilter(whitelist=["*.example.com"])
        assert f.is_allowed("sub.example.com")
        assert not f.is_allowed("other.com")

    def test_blacklist_takes_precedence(self):
        f = ScanFilter(
            whitelist=["*.example.com"],
            blacklist=["admin.example.com"]
        )
        assert not f.is_allowed("admin.example.com")
        assert f.is_allowed("www.example.com")

    def test_filter_targets(self):
        f = ScanFilter(blacklist=["*.internal"])
        targets = ["a.com", "b.internal", "c.com"]
        assert f.filter_targets(targets) == ["a.com", "c.com"]


class TestConfidenceScoring:
    """Tests for vulnerability confidence scoring."""

    def test_base_score_nuclei(self):
        score = calculate_confidence("nuclei")
        assert score == 60

    def test_base_score_xray(self):
        score = calculate_confidence("xray")
        assert score == 65

    def test_evidence_bonus(self):
        score = calculate_confidence("nuclei", has_evidence=True)
        assert score == 75

    def test_multi_source_bonus(self):
        score = calculate_confidence("nuclei", multi_source=True)
        assert score == 80

    def test_max_score_capped(self):
        score = calculate_confidence(
            "manual",
            has_evidence=True,
            multi_source=True,
            historical_hit=True
        )
        assert score == 100


class TestMergeSources:
    """Tests for merging findings from multiple sources."""

    def test_empty_findings(self):
        assert merge_sources([]) == {}

    def test_single_finding(self):
        result = merge_sources([{"scanner": "nuclei", "severity": "high"}])
        assert result["scanner"] == "nuclei"

    def test_keeps_higher_severity(self):
        findings = [
            {"scanner": "nuclei", "severity": "medium"},
            {"scanner": "xray", "severity": "high"},
        ]
        result = merge_sources(findings)
        assert result["severity"] == "high"
        assert result["multi_source"] is True
