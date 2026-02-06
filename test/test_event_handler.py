"""Tests for event handler task delegation."""

from worker.app.tasks import event_handler


def test_process_event_task_delegates_to_internal_handler(monkeypatch):
    captured = {}

    def fake_processor(*, project_id, event_type, event_data):
        captured["project_id"] = project_id
        captured["event_type"] = event_type
        captured["event_data"] = event_data
        return {"status": "ok"}

    monkeypatch.setattr(event_handler, "_process_event_internal", fake_processor)

    result = event_handler.process_event.run("project-1", "scan_completed", {"task_id": "t-1"})

    assert result == {"status": "ok"}
    assert captured == {
        "project_id": "project-1",
        "event_type": "scan_completed",
        "event_data": {"task_id": "t-1"},
    }


def test_emit_asset_event_builds_payload_and_delegates(monkeypatch):
    captured = {}

    def fake_processor(*, project_id, event_type, event_data):
        captured["project_id"] = project_id
        captured["event_type"] = event_type
        captured["event_data"] = event_data
        return {"status": "ok"}

    monkeypatch.setattr(event_handler, "_process_event_internal", fake_processor)

    result = event_handler.emit_asset_event.run(
        "project-1",
        "asset_created",
        "subdomain",
        "asset-1",
        {"source": "scanner"},
    )

    assert result == {"status": "ok"}
    assert captured == {
        "project_id": "project-1",
        "event_type": "asset_created",
        "event_data": {
            "asset_type": "subdomain",
            "asset_id": "asset-1",
            "source": "scanner",
        },
    }


def test_emit_scan_event_builds_payload_and_delegates(monkeypatch):
    captured = {}

    def fake_processor(*, project_id, event_type, event_data):
        captured["project_id"] = project_id
        captured["event_type"] = event_type
        captured["event_data"] = event_data
        return {"status": "ok"}

    monkeypatch.setattr(event_handler, "_process_event_internal", fake_processor)

    result = event_handler.emit_scan_event.run(
        "project-1",
        "scan_completed",
        "scan-1",
        "http_probe",
        {"alive": 10},
    )

    assert result == {"status": "ok"}
    assert captured == {
        "project_id": "project-1",
        "event_type": "scan_completed",
        "event_data": {
            "scan_task_id": "scan-1",
            "task_type": "http_probe",
            "alive": 10,
        },
    }
