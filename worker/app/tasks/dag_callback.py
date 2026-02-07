"""Utilities for linking scan task completion back to DAG execution."""

import logging
from uuid import UUID

from server.app.crud import dag_execution as crud_execution

logger = logging.getLogger(__name__)


def notify_dag_node_completion(db, scan_task_id: UUID, success: bool) -> None:
    """
    Notify DAG executor when a scan task that belongs to a DAG node completes.

    This is a best-effort callback and should not break scan task completion path.
    """
    try:
        matched = crud_execution.get_execution_node_by_task_id(db=db, scan_task_id=scan_task_id)
        if not matched:
            return

        execution, node_id = matched
        from worker.app.tasks import dag_executor

        dag_executor.on_node_completed.delay(
            execution_id=str(execution.id),
            node_id=node_id,
            success=success,
        )
    except Exception as exc:
        logger.warning(f"Failed to notify DAG callback for task {scan_task_id}: {exc}")
