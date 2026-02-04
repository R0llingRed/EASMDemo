from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import dag_template as crud_template
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.dag_template import DAGTemplateCreate, DAGTemplateOut, DAGTemplateUpdate

router = APIRouter(prefix="/projects/{project_id}/dag-templates", tags=["dag-templates"])


@router.post("", response_model=DAGTemplateOut, status_code=201)
def create_template(
    body: DAGTemplateCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """创建DAG模板"""
    # 验证节点定义
    node_ids = set()
    for node in body.nodes:
        if node.id in node_ids:
            raise HTTPException(status_code=400, detail=f"Duplicate node id: {node.id}")
        node_ids.add(node.id)

    # 验证依赖关系
    for node in body.nodes:
        for dep in node.depends_on:
            if dep not in node_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Node '{node.id}' depends on unknown node '{dep}'",
                )

    template = crud_template.create_dag_template(
        db=db,
        project_id=project.id,
        name=body.name,
        description=body.description,
        nodes=[n.model_dump() for n in body.nodes],
        edges=body.edges,
        is_system=False,  # 用户创建的不能是系统模板
        enabled=body.enabled,
    )
    return template


@router.get("", response_model=Page[DAGTemplateOut])
def list_templates(
    include_global: bool = True,
    enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出DAG模板（包含全局模板）"""
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    items = crud_template.list_dag_templates(
        db=db,
        project_id=project.id,
        include_global=include_global,
        enabled=enabled,
        skip=skip,
        limit=limit,
    )
    total = crud_template.count_dag_templates(
        db=db,
        project_id=project.id,
        include_global=include_global,
        enabled=enabled,
    )
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/{template_id}", response_model=DAGTemplateOut)
def get_template(
    template_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取DAG模板"""
    template = crud_template.get_dag_template(db=db, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    # 允许访问全局模板或项目模板
    if template.project_id and template.project_id != project.id:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.patch("/{template_id}", response_model=DAGTemplateOut)
def update_template(
    template_id: UUID,
    body: DAGTemplateUpdate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """更新DAG模板"""
    template = crud_template.get_dag_template(db=db, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.project_id and template.project_id != project.id:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system template")

    # 如果更新节点，需要验证
    if body.nodes:
        node_ids = set()
        for node in body.nodes:
            if node.id in node_ids:
                raise HTTPException(status_code=400, detail=f"Duplicate node id: {node.id}")
            node_ids.add(node.id)
        for node in body.nodes:
            for dep in node.depends_on:
                if dep not in node_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Node '{node.id}' depends on unknown node '{dep}'",
                    )

    update_data = body.model_dump(exclude_unset=True)
    if "nodes" in update_data and update_data["nodes"]:
        update_data["nodes"] = [n.model_dump() if hasattr(n, "model_dump") else n for n in update_data["nodes"]]

    updated = crud_template.update_dag_template(db=db, template=template, **update_data)
    return updated


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """删除DAG模板"""
    template = crud_template.get_dag_template(db=db, template_id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.project_id and template.project_id != project.id:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system template")
    crud_template.delete_dag_template(db=db, template=template)
    return None
