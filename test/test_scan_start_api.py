from types import SimpleNamespace
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")

from fastapi import HTTPException

from server.app.api import scans as scans_api


def test_start_scan_marks_running_before_dispatch(monkeypatch):
    project_id = uuid4()
    task = SimpleNamespace(id=uuid4(), project_id=project_id, status="pending")
    started_task = SimpleNamespace(id=task.id, project_id=project_id, status="running")

    monkeypatch.setattr(scans_api.crud_scan_task, "get_scan_task", lambda db, task_id: task)
    monkeypatch.setattr(
        scans_api.crud_scan_task,
        "start_scan_task",
        lambda db, task_id, project_id: started_task,
    )

    dispatched = []
    monkeypatch.setattr(scans_api, "_dispatch_scan_task", lambda t: dispatched.append(t.id))

    result = scans_api.start_scan(task.id, project=SimpleNamespace(id=project_id), db=None)

    assert result.status == "running"
    assert dispatched == [task.id]


def test_start_scan_records_dispatch_failure(monkeypatch):
    project_id = uuid4()
    task = SimpleNamespace(id=uuid4(), project_id=project_id, status="pending")
    started_task = SimpleNamespace(id=task.id, project_id=project_id, status="running")

    monkeypatch.setattr(scans_api.crud_scan_task, "get_scan_task", lambda db, task_id: task)
    monkeypatch.setattr(
        scans_api.crud_scan_task,
        "start_scan_task",
        lambda db, task_id, project_id: started_task,
    )

    def fail_dispatch(_task):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(scans_api, "_dispatch_scan_task", fail_dispatch)

    updated = {}

    def fake_update(db, task_id, status, error_message=None, result_summary=None):
        updated["task_id"] = task_id
        updated["status"] = status
        updated["error_message"] = error_message
        return started_task

    monkeypatch.setattr(scans_api.crud_scan_task, "update_scan_task_status", fake_update)

    with pytest.raises(HTTPException) as exc:
        scans_api.start_scan(task.id, project=SimpleNamespace(id=project_id), db=None)

    assert exc.value.status_code == 500
    assert "broker unavailable" in exc.value.detail
    assert updated["task_id"] == task.id
    assert updated["status"] == "failed"
    assert "broker unavailable" in (updated["error_message"] or "")


def test_start_scan_rejects_non_pending_task(monkeypatch):
    project_id = uuid4()
    task = SimpleNamespace(id=uuid4(), project_id=project_id, status="running")

    monkeypatch.setattr(scans_api.crud_scan_task, "get_scan_task", lambda db, task_id: task)

    with pytest.raises(HTTPException) as exc:
        scans_api.start_scan(task.id, project=SimpleNamespace(id=project_id), db=None)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Task is not in pending status"
