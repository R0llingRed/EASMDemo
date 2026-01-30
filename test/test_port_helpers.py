"""Tests for port scanning helper functions."""


# Copy function from worker/app/tasks/scan.py for standalone testing
def _guess_service(port: int) -> str:
    """Guess service name by port number."""
    services = {
        21: "ftp",
        22: "ssh",
        23: "telnet",
        25: "smtp",
        53: "dns",
        80: "http",
        110: "pop3",
        143: "imap",
        443: "https",
        3306: "mysql",
        3389: "rdp",
        5432: "postgresql",
        6379: "redis",
        8080: "http-proxy",
        8443: "https-alt",
    }
    return services.get(port, "unknown")


class TestGuessService:
    """Test service guessing by port."""

    def test_common_ports(self):
        """Test common port to service mapping."""
        assert _guess_service(22) == "ssh"
        assert _guess_service(80) == "http"
        assert _guess_service(443) == "https"
        assert _guess_service(3306) == "mysql"

    def test_unknown_port(self):
        """Test unknown port returns 'unknown'."""
        assert _guess_service(12345) == "unknown"
