"""Tests for scan task -> DAG completion callback bridge."""

from types import SimpleNamespace
from uuid import uuid4

from worker.app.tasks import dag_callback


def test_notify_dag_node_completion_dispatches_callback(monkeypatch):
    from worker.app.tasks import dag_executor

    execution_id = uuid4()
    scan_task_id = uuid4()
    calls = []

    monkeypatch.setattr(
        dag_callback.crud_execution,
        "get_execution_node_by_task_id",
        lambda db, scan_task_id: (SimpleNamespace(id=execution_id), "node-a"),
    )
    monkeypatch.setattr(
        dag_executor,
        "on_node_completed",
        SimpleNamespace(delay=lambda **kwargs: calls.append(kwargs)),
    )

    dag_callback.notify_dag_node_completion(db=None, scan_task_id=scan_task_id, success=True)

    assert len(calls) == 1
    assert calls[0]["execution_id"] == str(execution_id)
    assert calls[0]["node_id"] == "node-a"
    assert calls[0]["success"] is True


def test_notify_dag_node_completion_noop_when_task_not_in_dag(monkeypatch):
    from worker.app.tasks import dag_executor

    scan_task_id = uuid4()
    calls = []

    monkeypatch.setattr(
        dag_callback.crud_execution,
        "get_execution_node_by_task_id",
        lambda db, scan_task_id: None,
    )
    monkeypatch.setattr(
        dag_executor,
        "on_node_completed",
        SimpleNamespace(delay=lambda **kwargs: calls.append(kwargs)),
    )

    dag_callback.notify_dag_node_completion(db=None, scan_task_id=scan_task_id, success=False)

    assert calls == []
