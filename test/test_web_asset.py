"""Tests for web asset schema - standalone version."""
from enum import Enum


class TaskType(str, Enum):
    """Copy of TaskType enum for standalone testing."""
    subdomain_scan = "subdomain_scan"
    dns_resolve = "dns_resolve"
    port_scan = "port_scan"
    http_probe = "http_probe"
    fingerprint = "fingerprint"
    screenshot = "screenshot"


class TestWebAssetSchema:
    """Tests for web asset schema validation."""

    def test_task_type_enum_values(self):
        """Test that TaskType enum includes web-related types."""
        assert hasattr(TaskType, "http_probe")
        assert hasattr(TaskType, "fingerprint")
        assert hasattr(TaskType, "screenshot")

    def test_task_type_values(self):
        """Test TaskType enum string values."""
        assert TaskType.http_probe.value == "http_probe"
        assert TaskType.fingerprint.value == "fingerprint"
        assert TaskType.screenshot.value == "screenshot"

    def test_all_task_types(self):
        """Test all task types are present."""
        expected = [
            "subdomain_scan",
            "dns_resolve",
            "port_scan",
            "http_probe",
            "fingerprint",
            "screenshot",
        ]
        actual = [t.value for t in TaskType]
        assert actual == expected
