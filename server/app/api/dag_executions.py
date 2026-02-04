from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import dag_execution as crud_execution
from server.app.crud import dag_template as crud_template
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.dag_execution import DAGExecutionCreate, DAGExecutionOut
from worker.app.tasks import dag_executor

router = APIRouter(prefix="/projects/{project_id}/dag-executions", tags=["dag-executions"])


@router.post("", response_model=DAGExecutionOut, status_code=201)
def create_execution(
    body: DAGExecutionCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """创建DAG执行实例"""
    # 验证模板存在
    template = crud_template.get_dag_template(db=db, template_id=body.dag_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="DAG template not found")
    if template.project_id and template.project_id != project.id:
        raise HTTPException(status_code=404, detail="DAG template not found")
    if not template.enabled:
        raise HTTPException(status_code=400, detail="DAG template is disabled")

    # 初始化节点状态
    initial_node_states = {}
    for node in template.nodes:
        node_id = node.get("id") if isinstance(node, dict) else node.id
        initial_node_states[node_id] = "pending"

    execution = crud_execution.create_dag_execution(
        db=db,
        project_id=project.id,
        dag_template_id=body.dag_template_id,
        trigger_type=body.trigger_type.value,
        trigger_event=body.trigger_event,
        input_config=body.input_config,
        initial_node_states=initial_node_states,
    )
    return execution


@router.get("", response_model=Page[DAGExecutionOut])
def list_executions(
    dag_template_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出DAG执行实例"""
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    items = crud_execution.list_dag_executions(
        db=db,
        project_id=project.id,
        dag_template_id=dag_template_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    total = crud_execution.count_dag_executions(
        db=db,
        project_id=project.id,
        dag_template_id=dag_template_id,
        status=status,
    )
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{execution_id}", response_model=DAGExecutionOut)
def get_execution(
    execution_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取DAG执行实例"""
    execution = crud_execution.get_dag_execution(db=db, execution_id=execution_id)
    if not execution or execution.project_id != project.id:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/{execution_id}/start", response_model=DAGExecutionOut)
def start_execution(
    execution_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """启动DAG执行"""
    execution = crud_execution.get_dag_execution(db=db, execution_id=execution_id)
    if not execution or execution.project_id != project.id:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.status != "pending":
        raise HTTPException(status_code=400, detail="Execution is not in pending status")

    # 更新状态为运行中
    execution = crud_execution.update_execution_status(db=db, execution=execution, status="running")

    # 异步启动DAG执行
    dag_executor.execute_dag.delay(str(execution.id))

    return execution


@router.post("/{execution_id}/cancel", response_model=DAGExecutionOut)
def cancel_execution(
    execution_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """取消DAG执行"""
    execution = crud_execution.get_dag_execution(db=db, execution_id=execution_id)
    if not execution or execution.project_id != project.id:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail="Execution cannot be cancelled")

    execution = crud_execution.update_execution_status(db=db, execution=execution, status="cancelled")
    return execution
