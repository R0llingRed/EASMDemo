"""Tests for fingerprint identification logic."""
from typing import List


def _check_title_fingerprints(title: str, fingerprints: List[str]) -> None:
    """Check title for common fingerprints."""
    patterns = {
        "wordpress": "WordPress",
        "drupal": "Drupal",
        "joomla": "Joomla",
        "phpmyadmin": "phpMyAdmin",
        "weblogic": "WebLogic",
        "jenkins": "Jenkins",
        "gitlab": "GitLab",
        "grafana": "Grafana",
        "kibana": "Kibana",
        "zabbix": "Zabbix",
        "nagios": "Nagios",
        "confluence": "Confluence",
        "jira": "Jira",
    }
    for pattern, name in patterns.items():
        if pattern in title:
            fingerprints.append(name)


class TestTitleFingerprints:
    """Tests for title-based fingerprint detection."""

    def test_wordpress_detection(self):
        fingerprints = []
        _check_title_fingerprints("my wordpress blog", fingerprints)
        assert "WordPress" in fingerprints

    def test_jenkins_detection(self):
        fingerprints = []
        _check_title_fingerprints("jenkins dashboard", fingerprints)
        assert "Jenkins" in fingerprints

    def test_gitlab_detection(self):
        fingerprints = []
        _check_title_fingerprints("gitlab - sign in", fingerprints)
        assert "GitLab" in fingerprints

    def test_grafana_detection(self):
        fingerprints = []
        _check_title_fingerprints("grafana - home", fingerprints)
        assert "Grafana" in fingerprints

    def test_multiple_fingerprints(self):
        fingerprints = []
        _check_title_fingerprints("wordpress with grafana", fingerprints)
        assert "WordPress" in fingerprints
        assert "Grafana" in fingerprints

    def test_no_fingerprint(self):
        fingerprints = []
        _check_title_fingerprints("my custom website", fingerprints)
        assert len(fingerprints) == 0

    def test_case_sensitivity(self):
        fingerprints = []
        _check_title_fingerprints("WORDPRESS", fingerprints)
        # Pattern is lowercase, so uppercase won't match
        assert "WordPress" not in fingerprints

    def test_jira_detection(self):
        fingerprints = []
        _check_title_fingerprints("jira - project board", fingerprints)
        assert "Jira" in fingerprints

    def test_confluence_detection(self):
        fingerprints = []
        _check_title_fingerprints("confluence - documentation", fingerprints)
        assert "Confluence" in fingerprints
