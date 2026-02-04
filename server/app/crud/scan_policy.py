from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.models.scan_policy import ScanPolicy


def create_scan_policy(
    db: Session,
    project_id: UUID,
    name: str,
    description: Optional[str] = None,
    scan_config: Optional[dict] = None,
    dag_template_id: Optional[UUID] = None,
    is_default: bool = False,
    enabled: bool = True,
) -> ScanPolicy:
    """创建扫描策略"""
    # 如果设置为默认，先取消其他默认策略
    if is_default:
        db.query(ScanPolicy).filter(
            ScanPolicy.project_id == project_id, ScanPolicy.is_default == True
        ).update({"is_default": False})

    policy = ScanPolicy(
        project_id=project_id,
        name=name,
        description=description,
        scan_config=scan_config or {},
        dag_template_id=dag_template_id,
        is_default=is_default,
        enabled=enabled,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_scan_policy(db: Session, policy_id: UUID) -> Optional[ScanPolicy]:
    """获取扫描策略"""
    return db.query(ScanPolicy).filter(ScanPolicy.id == policy_id).first()


def get_default_policy(db: Session, project_id: UUID) -> Optional[ScanPolicy]:
    """获取项目默认策略"""
    return (
        db.query(ScanPolicy)
        .filter(ScanPolicy.project_id == project_id, ScanPolicy.is_default == True)
        .first()
    )


def list_scan_policies(
    db: Session,
    project_id: UUID,
    enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[ScanPolicy]:
    """列出扫描策略"""
    query = db.query(ScanPolicy).filter(ScanPolicy.project_id == project_id)
    if enabled is not None:
        query = query.filter(ScanPolicy.enabled == enabled)
    return query.order_by(ScanPolicy.created_at.desc()).offset(skip).limit(limit).all()


def count_scan_policies(
    db: Session,
    project_id: UUID,
    enabled: Optional[bool] = None,
) -> int:
    """统计扫描策略数量"""
    query = db.query(ScanPolicy).filter(ScanPolicy.project_id == project_id)
    if enabled is not None:
        query = query.filter(ScanPolicy.enabled == enabled)
    return query.count()


def update_scan_policy(
    db: Session,
    policy: ScanPolicy,
    **kwargs,
) -> ScanPolicy:
    """更新扫描策略"""
    # 如果设置为默认，先取消其他默认策略
    if kwargs.get("is_default"):
        db.query(ScanPolicy).filter(
            ScanPolicy.project_id == policy.project_id,
            ScanPolicy.is_default == True,
            ScanPolicy.id != policy.id,
        ).update({"is_default": False})

    for key, value in kwargs.items():
        if value is not None and hasattr(policy, key):
            setattr(policy, key, value)
    db.commit()
    db.refresh(policy)
    return policy


def delete_scan_policy(db: Session, policy: ScanPolicy) -> None:
    """删除扫描策略"""
    db.delete(policy)
    db.commit()
