"""Tests for effective project/task rate limit resolution."""

from types import SimpleNamespace
from uuid import uuid4

from worker.app.utils import scan_helpers


def test_get_effective_rate_limit_config_merges_project_and_task(monkeypatch):
    project_id = uuid4()
    project = SimpleNamespace(
        rate_limit_config={"max_requests_per_second": 3, "max_concurrent_scans": 2}
    )

    monkeypatch.setattr(scan_helpers, "get_project", lambda db, project_id: project)

    result = scan_helpers.get_effective_rate_limit_config(
        db=None,
        project_id=project_id,
        task_config={"rate_limit_config": {"max_requests_per_second": 9}},
    )

    assert result == {"max_requests_per_second": 9, "max_concurrent_scans": 2}


def test_wait_for_project_rate_limit_uses_merged_config(monkeypatch):
    project_id = uuid4()
    project = SimpleNamespace(
        rate_limit_config={"max_requests_per_second": 4, "max_concurrent_scans": 1}
    )
    captured = {}

    monkeypatch.setattr(scan_helpers, "get_project", lambda db, project_id: project)

    def fake_wait_for_rate_limit(project_id, config, max_wait):
        captured["project_id"] = project_id
        captured["config"] = config
        captured["max_wait"] = max_wait
        return True

    monkeypatch.setattr(scan_helpers, "wait_for_rate_limit", fake_wait_for_rate_limit)

    ok = scan_helpers.wait_for_project_rate_limit(
        db=None,
        project_id=project_id,
        task_config={"rate_limit_config": {"max_concurrent_scans": 5}},
        max_wait=12.5,
    )

    assert ok is True
    assert captured["project_id"] == project_id
    assert captured["config"] == {"max_requests_per_second": 4, "max_concurrent_scans": 5}
    assert captured["max_wait"] == 12.5
