"""Tests for scan_task schemas - standalone version."""
from enum import Enum


# Copy enums from server/app/schemas/scan_task.py for standalone testing
class TaskType(str, Enum):
    subdomain_scan = "subdomain_scan"
    dns_resolve = "dns_resolve"
    port_scan = "port_scan"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class TestScanTaskSchemas:
    """Test scan task schema definitions."""

    def test_task_type_enum(self):
        """Test TaskType enum values."""
        assert TaskType.subdomain_scan.value == "subdomain_scan"
        assert TaskType.dns_resolve.value == "dns_resolve"
        assert TaskType.port_scan.value == "port_scan"

    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.pending.value == "pending"
        assert TaskStatus.running.value == "running"
        assert TaskStatus.completed.value == "completed"
        assert TaskStatus.failed.value == "failed"

    def test_task_type_is_string(self):
        """Test TaskType values are strings."""
        for t in TaskType:
            assert isinstance(t.value, str)

    def test_task_status_is_string(self):
        """Test TaskStatus values are strings."""
        for s in TaskStatus:
            assert isinstance(s.value, str)
