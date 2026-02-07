"""
DAG Executor - Celery task for executing DAG workflows

This module handles the execution of DAG (Directed Acyclic Graph) workflows,
managing node dependencies and orchestrating scan tasks.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from celery import shared_task
from sqlalchemy.orm import Session

from server.app.crud import dag_execution as crud_execution
from server.app.crud import dag_template as crud_template
from server.app.crud import scan_task as crud_scan_task
from server.app.models.dag_execution import DAGExecution
from worker.app.celery_app import celery_app
from worker.app.tasks import fingerprint as fingerprint_tasks
from worker.app.tasks import http_probe as http_probe_tasks
from worker.app.tasks import js_api_discovery as js_api_discovery_tasks
from worker.app.tasks import nuclei_scan as nuclei_tasks
from worker.app.tasks import scan as scan_tasks
from worker.app.tasks import screenshot as screenshot_tasks
from worker.app.tasks import xray_scan as xray_tasks

logger = logging.getLogger(__name__)

# 任务类型到处理器的映射
TASK_DISPATCHERS = {
    "subdomain_scan": scan_tasks.run_scan,
    "dns_resolve": scan_tasks.run_scan,
    "port_scan": scan_tasks.run_scan,
    "http_probe": http_probe_tasks.run_http_probe,
    "fingerprint": fingerprint_tasks.run_fingerprint,
    "screenshot": screenshot_tasks.run_screenshot,
    "nuclei_scan": nuclei_tasks.run_nuclei_scan,
    "xray_scan": xray_tasks.run_xray_scan,
    "js_api_discovery": js_api_discovery_tasks.run_js_api_discovery,
}


def _to_celery_priority(priority: int) -> int:
    """Convert priority range (1-10) to Celery range (0-9)."""
    normalized = max(1, min(10, int(priority or 5)))
    return normalized - 1


def get_db() -> Session:
    """获取数据库会话"""
    from server.app.db.session import SessionLocal

    return SessionLocal()


def detect_cycle(nodes: List[Dict[str, Any]]) -> bool:
    """
    检测 DAG 中是否存在循环依赖
    
    Args:
        nodes: 节点列表
        
    Returns:
        True 如果存在循环，False 如果不存在
    """
    graph = {}
    for node in nodes:
        node_id = node.get("id") if isinstance(node, dict) else node.id
        depends_on = node.get("depends_on", []) if isinstance(node, dict) else getattr(node, "depends_on", [])
        graph[node_id] = set(depends_on)
    
    visited = set()
    rec_stack = set()
    
    def dfs(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)
        
        for dep in graph.get(node_id, set()):
            if dep not in visited:
                if dfs(dep):
                    return True
            elif dep in rec_stack:
                return True
        
        rec_stack.remove(node_id)
        return False
    
    for node_id in graph:
        if node_id not in visited:
            if dfs(node_id):
                return True
    
    return False


def build_dependency_graph(nodes: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    """
    构建依赖图

    Returns:
        Dict[node_id, Set[依赖的node_id]]
    """
    graph = {}
    for node in nodes:
        node_id = node.get("id")
        depends_on = node.get("depends_on", [])
        graph[node_id] = set(depends_on)
    return graph


def get_ready_nodes(
    nodes: List[Dict[str, Any]],
    node_states: Dict[str, str],
    dependency_graph: Dict[str, Set[str]],
) -> List[Dict[str, Any]]:
    """
    获取可以执行的节点（所有依赖已完成且自身pending）

    Returns:
        可执行节点列表
    """
    ready = []
    for node in nodes:
        node_id = node.get("id")
        # 节点必须是pending状态
        if node_states.get(node_id) != "pending":
            continue
        # 检查所有依赖是否已完成
        deps = dependency_graph.get(node_id, set())
        all_deps_completed = all(node_states.get(dep) == "completed" for dep in deps)
        if all_deps_completed:
            ready.append(node)
    return ready


def check_execution_complete(node_states: Dict[str, str]) -> tuple[bool, bool]:
    """
    检查执行是否完成

    Returns:
        (is_complete, is_success)
    """
    if not node_states:
        return False, False

    all_completed = all(s in ("completed", "skipped", "failed") for s in node_states.values())
    has_failure = any(s == "failed" for s in node_states.values())

    if all_completed:
        return True, not has_failure
    return False, False


def mark_blocked_nodes_as_skipped(
    nodes: List[Dict[str, Any]],
    node_states: Dict[str, str],
    dependency_graph: Dict[str, Set[str]],
) -> List[str]:
    """
    Mark pending nodes as skipped if any dependency has failed.

    Returns:
        List of node_ids that were updated to skipped.
    """
    changed_nodes: List[str] = []

    for node in nodes:
        node_id = node.get("id")
        if node_states.get(node_id) != "pending":
            continue
        deps = dependency_graph.get(node_id, set())
        if any(node_states.get(dep) in ("failed", "skipped") for dep in deps):
            node_states[node_id] = "skipped"
            changed_nodes.append(node_id)

    return changed_nodes


def dispatch_scan_task(
    db: Session,
    project_id: UUID,
    task_type: str,
    config: Dict[str, Any],
) -> Optional[UUID]:
    """
    创建并分发扫描任务

    Returns:
        scan_task_id
    """
    priority = int(config.get("priority", 5)) if isinstance(config, dict) else 5

    # 创建 scan_task
    task = crud_scan_task.create_scan_task(
        db=db,
        project_id=project_id,
        task_type=task_type,
        config=config,
        priority=priority,
    )

    # 使用映射分发到对应的 Celery 任务
    task_id = str(task.id)
    dispatcher = TASK_DISPATCHERS.get(task_type)
    
    if dispatcher:
        dispatcher.apply_async(args=[task_id], priority=_to_celery_priority(priority))
        return task.id
    else:
        logger.warning(f"Unknown task type: {task_type}")
        return None


@celery_app.task(bind=True, name="worker.app.tasks.dag_executor.execute_dag")
def execute_dag(self, execution_id: str) -> Dict[str, Any]:
    """
    执行 DAG 工作流

    Args:
        execution_id: DAG执行实例ID
    """
    db = get_db()
    execution = None  # 初始化以避免异常处理时的未定义引用
    try:
        execution = crud_execution.get_dag_execution(db=db, execution_id=UUID(execution_id))
        if not execution:
            logger.error(f"DAG execution not found: {execution_id}")
            return {"status": "error", "message": "Execution not found"}

        # 获取模板
        template = crud_template.get_dag_template(db=db, template_id=execution.dag_template_id)
        if not template:
            crud_execution.update_execution_status(
                db=db, execution=execution, status="failed", error_message="Template not found"
            )
            return {"status": "error", "message": "Template not found"}

        nodes = template.nodes
        if not nodes:
            crud_execution.update_execution_status(
                db=db, execution=execution, status="completed"
            )
            return {"status": "completed", "message": "No nodes to execute"}

        # 构建依赖图
        dependency_graph = build_dependency_graph(nodes)
        node_states = dict(execution.node_states) if execution.node_states else {}

        # 初始化节点状态
        for node in nodes:
            node_id = node.get("id")
            if node_id not in node_states:
                node_states[node_id] = "pending"

        # 获取可执行节点
        ready_nodes = get_ready_nodes(nodes, node_states, dependency_graph)

        if not ready_nodes:
            skipped_nodes = mark_blocked_nodes_as_skipped(nodes, node_states, dependency_graph)
            for node_id in skipped_nodes:
                crud_execution.update_node_state(
                    db=db,
                    execution=execution,
                    node_id=node_id,
                    state="skipped",
                )

            # 检查是否已完成
            is_complete, is_success = check_execution_complete(node_states)
            if is_complete:
                status = "completed" if is_success else "failed"
                crud_execution.update_execution_status(db=db, execution=execution, status=status)
                return {"status": status}
            else:
                # 可能有节点正在运行
                return {"status": "waiting", "message": "Waiting for running nodes"}

        # 执行就绪节点
        input_config = execution.input_config or {}
        for node in ready_nodes:
            node_id = node.get("id")
            task_type = node.get("task_type")
            node_config = {**input_config, **node.get("config", {})}

            # 更新节点状态为 running
            crud_execution.update_node_state(db=db, execution=execution, node_id=node_id, state="running")
            node_states[node_id] = "running"

            # 分发扫描任务
            task_id = dispatch_scan_task(
                db=db,
                project_id=execution.project_id,
                task_type=task_type,
                config=node_config,
            )

            if task_id:
                crud_execution.update_node_state(
                    db=db, execution=execution, node_id=node_id, state="running", task_id=task_id
                )
                logger.info(f"Dispatched task {task_type} for node {node_id}, task_id={task_id}")
            else:
                crud_execution.update_node_state(
                    db=db, execution=execution, node_id=node_id, state="failed"
                )
                node_states[node_id] = "failed"
                logger.error(f"Failed to dispatch task for node {node_id}")

        return {
            "status": "running",
            "dispatched_nodes": [n.get("id") for n in ready_nodes],
        }

    except Exception as e:
        logger.exception(f"DAG execution error: {e}")
        if execution:
            crud_execution.update_execution_status(
                db=db, execution=execution, status="failed", error_message=str(e)
            )
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="worker.app.tasks.dag_executor.on_node_completed")
def on_node_completed(self, execution_id: str, node_id: str, success: bool = True) -> Dict[str, Any]:
    """
    节点完成回调 - 检查并触发下游节点

    Args:
        execution_id: DAG执行实例ID
        node_id: 完成的节点ID
        success: 是否成功
    """
    db = get_db()
    try:
        execution = crud_execution.get_dag_execution(db=db, execution_id=UUID(execution_id))
        if not execution:
            return {"status": "error", "message": "Execution not found"}

        # 更新节点状态
        state = "completed" if success else "failed"
        crud_execution.update_node_state(db=db, execution=execution, node_id=node_id, state=state)

        # 重新获取执行实例以获取最新状态
        db.refresh(execution)

        # 继续执行DAG
        execute_dag.delay(execution_id)

        return {"status": "ok", "node_id": node_id, "state": state}

    except Exception as e:
        logger.exception(f"on_node_completed error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
