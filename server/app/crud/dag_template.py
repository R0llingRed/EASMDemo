from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.models.dag_template import DAGTemplate


def create_dag_template(
    db: Session,
    name: str,
    nodes: list,
    project_id: Optional[UUID] = None,
    description: Optional[str] = None,
    edges: Optional[list] = None,
    is_system: bool = False,
    enabled: bool = True,
) -> DAGTemplate:
    """创建DAG模板"""
    template = DAGTemplate(
        project_id=project_id,
        name=name,
        description=description,
        nodes=nodes,
        edges=edges or [],
        is_system=is_system,
        enabled=enabled,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def get_dag_template(db: Session, template_id: UUID) -> Optional[DAGTemplate]:
    """获取DAG模板"""
    return db.query(DAGTemplate).filter(DAGTemplate.id == template_id).first()


def list_dag_templates(
    db: Session,
    project_id: Optional[UUID] = None,
    include_global: bool = True,
    enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[DAGTemplate]:
    """列出DAG模板（包含全局模板）"""
    query = db.query(DAGTemplate)

    if project_id and include_global:
        # 项目模板 + 全局模板
        query = query.filter(
            (DAGTemplate.project_id == project_id) | (DAGTemplate.project_id.is_(None))
        )
    elif project_id:
        # 仅项目模板
        query = query.filter(DAGTemplate.project_id == project_id)
    else:
        # 仅全局模板
        query = query.filter(DAGTemplate.project_id.is_(None))

    if enabled is not None:
        query = query.filter(DAGTemplate.enabled == enabled)

    return query.order_by(DAGTemplate.is_system.desc(), DAGTemplate.created_at.desc()).offset(skip).limit(limit).all()


def count_dag_templates(
    db: Session,
    project_id: Optional[UUID] = None,
    include_global: bool = True,
    enabled: Optional[bool] = None,
) -> int:
    """统计DAG模板数量"""
    query = db.query(DAGTemplate)

    if project_id and include_global:
        query = query.filter(
            (DAGTemplate.project_id == project_id) | (DAGTemplate.project_id.is_(None))
        )
    elif project_id:
        query = query.filter(DAGTemplate.project_id == project_id)
    else:
        query = query.filter(DAGTemplate.project_id.is_(None))

    if enabled is not None:
        query = query.filter(DAGTemplate.enabled == enabled)

    return query.count()


def update_dag_template(
    db: Session,
    template: DAGTemplate,
    **kwargs,
) -> DAGTemplate:
    """更新DAG模板"""
    for key, value in kwargs.items():
        if value is not None and hasattr(template, key):
            setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template


def delete_dag_template(db: Session, template: DAGTemplate) -> None:
    """删除DAG模板"""
    db.delete(template)
    db.commit()


def get_system_templates(db: Session) -> List[DAGTemplate]:
    """获取系统预置模板"""
    return (
        db.query(DAGTemplate)
        .filter(DAGTemplate.is_system == True, DAGTemplate.enabled == True)
        .all()
    )
