"""Tests for nmap output parsing."""
import re
from typing import Any, Dict, List


# Copy function from worker/app/tasks/scan.py for standalone testing
def _parse_nmap_output(output: str) -> List[Dict[str, Any]]:
    """Parse nmap grepable output."""
    open_ports = []
    for line in output.split("\n"):
        if "Ports:" in line:
            ports_section = line.split("Ports:")[1]
            port_entries = ports_section.split(",")
            for entry in port_entries:
                match = re.search(r"(\d+)/open/tcp//([^/]*)", entry)
                if match:
                    open_ports.append({
                        "port": int(match.group(1)),
                        "service": match.group(2) or None,
                    })
    return open_ports


class TestParseNmapOutput:
    """Test nmap grepable output parsing."""

    def test_parse_single_port(self):
        """Test parsing single open port."""
        output = "Host: 192.168.1.1 () Ports: 80/open/tcp//http//"
        result = _parse_nmap_output(output)

        assert len(result) == 1
        assert result[0]["port"] == 80
        assert result[0]["service"] == "http"

    def test_parse_multiple_ports(self):
        """Test parsing multiple open ports."""
        output = "Host: 192.168.1.1 () Ports: 22/open/tcp//ssh//, 80/open/tcp//http//, 443/open/tcp//https//"
        result = _parse_nmap_output(output)

        assert len(result) == 3
        ports = [r["port"] for r in result]
        assert 22 in ports
        assert 80 in ports
        assert 443 in ports

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        result = _parse_nmap_output("")
        assert result == []
