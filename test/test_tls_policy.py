"""Tests for TLS verification policy in scanner helpers."""

import ssl

from worker.app.tasks import http_probe
from worker.app.utils.tls import create_ssl_context


def test_create_ssl_context_verify_enabled():
    ctx = create_ssl_context(verify_tls=True)
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_create_ssl_context_verify_disabled():
    ctx = create_ssl_context(verify_tls=False)
    assert ctx.verify_mode == ssl.CERT_NONE
    assert ctx.check_hostname is False


def test_probe_with_httpx_adds_insecure_flag_when_tls_verification_disabled(monkeypatch):
    captured = {}

    class FakeResult:
        returncode = 1
        stdout = ""

    def fake_run(command, **kwargs):
        captured["command"] = command
        return FakeResult()

    monkeypatch.setattr("subprocess.run", fake_run)

    result = http_probe._probe_with_httpx("https://example.com", verify_tls=False)

    assert result == {"is_alive": False}
    assert "-insecure" in captured["command"]


def test_probe_with_httpx_does_not_add_insecure_flag_when_tls_verification_enabled(monkeypatch):
    captured = {}

    class FakeResult:
        returncode = 1
        stdout = ""

    def fake_run(command, **kwargs):
        captured["command"] = command
        return FakeResult()

    monkeypatch.setattr("subprocess.run", fake_run)

    result = http_probe._probe_with_httpx("https://example.com", verify_tls=True)

    assert result == {"is_alive": False}
    assert "-insecure" not in captured["command"]
