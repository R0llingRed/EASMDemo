"""Tests for Round 8 task registration."""

from server.app.schemas.scan_task import TaskType
from worker.app.tasks import dag_executor


def test_scan_task_type_includes_js_api_discovery():
    assert TaskType.js_api_discovery.value == "js_api_discovery"


def test_dag_dispatchers_include_js_api_discovery():
    assert "js_api_discovery" in dag_executor.TASK_DISPATCHERS
