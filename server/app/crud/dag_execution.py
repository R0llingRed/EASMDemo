from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.models.dag_execution import DAGExecution


def create_dag_execution(
    db: Session,
    project_id: UUID,
    dag_template_id: UUID,
    trigger_type: str = "manual",
    trigger_event: Optional[dict] = None,
    input_config: Optional[dict] = None,
    initial_node_states: Optional[dict] = None,
) -> DAGExecution:
    """创建DAG执行实例"""
    execution = DAGExecution(
        project_id=project_id,
        dag_template_id=dag_template_id,
        trigger_type=trigger_type,
        trigger_event=trigger_event or {},
        input_config=input_config or {},
        node_states=initial_node_states or {},
        node_task_ids={},
        status="pending",
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def get_dag_execution(db: Session, execution_id: UUID) -> Optional[DAGExecution]:
    """获取DAG执行实例"""
    return db.query(DAGExecution).filter(DAGExecution.id == execution_id).first()


def list_dag_executions(
    db: Session,
    project_id: UUID,
    dag_template_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[DAGExecution]:
    """列出DAG执行实例"""
    query = db.query(DAGExecution).filter(DAGExecution.project_id == project_id)
    if dag_template_id:
        query = query.filter(DAGExecution.dag_template_id == dag_template_id)
    if status:
        query = query.filter(DAGExecution.status == status)
    return query.order_by(DAGExecution.created_at.desc()).offset(skip).limit(limit).all()


def count_dag_executions(
    db: Session,
    project_id: UUID,
    dag_template_id: Optional[UUID] = None,
    status: Optional[str] = None,
) -> int:
    """统计DAG执行实例数量"""
    query = db.query(DAGExecution).filter(DAGExecution.project_id == project_id)
    if dag_template_id:
        query = query.filter(DAGExecution.dag_template_id == dag_template_id)
    if status:
        query = query.filter(DAGExecution.status == status)
    return query.count()


def update_execution_status(
    db: Session,
    execution: DAGExecution,
    status: str,
    error_message: Optional[str] = None,
) -> DAGExecution:
    """更新执行状态"""
    execution.status = status
    if status == "running" and not execution.started_at:
        execution.started_at = datetime.utcnow()
    if status in ("completed", "failed", "cancelled"):
        execution.completed_at = datetime.utcnow()
    if error_message:
        execution.error_message = error_message
    db.commit()
    db.refresh(execution)
    return execution


def update_node_state(
    db: Session,
    execution: DAGExecution,
    node_id: str,
    state: str,
    task_id: Optional[UUID] = None,
) -> DAGExecution:
    """
    更新节点状态（带行级锁防止并发问题）
    """
    # 使用 SELECT FOR UPDATE 获取行级锁
    locked_execution = db.query(DAGExecution).filter(
        DAGExecution.id == execution.id
    ).with_for_update().first()
    
    if not locked_execution:
        db.refresh(execution)
        return execution
    
    node_states = dict(locked_execution.node_states) if locked_execution.node_states else {}
    node_states[node_id] = state
    locked_execution.node_states = node_states

    if task_id:
        node_task_ids = dict(locked_execution.node_task_ids) if locked_execution.node_task_ids else {}
        node_task_ids[node_id] = str(task_id)
        locked_execution.node_task_ids = node_task_ids

    db.commit()
    db.refresh(locked_execution)
    return locked_execution


def get_running_executions(db: Session, project_id: Optional[UUID] = None) -> List[DAGExecution]:
    """获取运行中的执行实例"""
    query = db.query(DAGExecution).filter(DAGExecution.status == "running")
    if project_id:
        query = query.filter(DAGExecution.project_id == project_id)
    return query.all()
