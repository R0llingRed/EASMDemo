"""Tests for API risk status workflow and audit trail."""

from datetime import datetime, timezone
from types import SimpleNamespace

from server.app.crud import api_risk_finding as crud_api_risk


class _FakeDB:
    def __init__(self):
        self.committed = False
        self.refreshed = False

    def commit(self):
        self.committed = True

    def refresh(self, _obj):
        self.refreshed = True


def test_update_api_risk_status_appends_history():
    db = _FakeDB()
    finding = SimpleNamespace(
        status="open",
        updated_by=None,
        resolution_notes=None,
        updated_at=datetime.now(timezone.utc),
        resolved_at=None,
        status_history=[],
    )

    updated = crud_api_risk.update_api_risk_status(
        db=db,
        finding=finding,
        status="investigating",
        updated_by="alice@example.com",
        resolution_notes=None,
    )

    assert updated.status == "investigating"
    assert updated.updated_by == "alice@example.com"
    assert updated.resolved_at is None
    assert len(updated.status_history) == 1
    assert updated.status_history[0]["from"] == "open"
    assert updated.status_history[0]["to"] == "investigating"
    assert db.committed is True
    assert db.refreshed is True


def test_update_api_risk_status_sets_resolved_at_for_terminal_states():
    db = _FakeDB()
    finding = SimpleNamespace(
        status="investigating",
        updated_by=None,
        resolution_notes=None,
        updated_at=datetime.now(timezone.utc),
        resolved_at=None,
        status_history=[],
    )

    updated = crud_api_risk.update_api_risk_status(
        db=db,
        finding=finding,
        status="resolved",
        updated_by="bob@example.com",
        resolution_notes="fixed in release 1.2.3",
    )

    assert updated.status == "resolved"
    assert updated.resolution_notes == "fixed in release 1.2.3"
    assert updated.resolved_at is not None
    assert len(updated.status_history) == 1
    assert updated.status_history[0]["to"] == "resolved"
