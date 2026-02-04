from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import scan_policy as crud_policy
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.scan_policy import ScanPolicyCreate, ScanPolicyOut, ScanPolicyUpdate

router = APIRouter(prefix="/projects/{project_id}/policies", tags=["policies"])


@router.post("", response_model=ScanPolicyOut, status_code=201)
def create_policy(
    body: ScanPolicyCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """创建扫描策略"""
    policy = crud_policy.create_scan_policy(
        db=db,
        project_id=project.id,
        name=body.name,
        description=body.description,
        scan_config=body.scan_config,
        dag_template_id=body.dag_template_id,
        is_default=body.is_default,
        enabled=body.enabled,
    )
    return policy


@router.get("", response_model=Page[ScanPolicyOut])
def list_policies(
    enabled: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出扫描策略"""
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    items = crud_policy.list_scan_policies(
        db=db,
        project_id=project.id,
        enabled=enabled,
        skip=skip,
        limit=limit,
    )
    total = crud_policy.count_scan_policies(
        db=db,
        project_id=project.id,
        enabled=enabled,
    )
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/default", response_model=ScanPolicyOut)
def get_default_policy(
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取默认策略"""
    policy = crud_policy.get_default_policy(db=db, project_id=project.id)
    if not policy:
        raise HTTPException(status_code=404, detail="No default policy found")
    return policy


@router.get("/{policy_id}", response_model=ScanPolicyOut)
def get_policy(
    policy_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取扫描策略"""
    policy = crud_policy.get_scan_policy(db=db, policy_id=policy_id)
    if not policy or policy.project_id != project.id:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/{policy_id}", response_model=ScanPolicyOut)
def update_policy(
    policy_id: UUID,
    body: ScanPolicyUpdate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """更新扫描策略"""
    policy = crud_policy.get_scan_policy(db=db, policy_id=policy_id)
    if not policy or policy.project_id != project.id:
        raise HTTPException(status_code=404, detail="Policy not found")
    updated = crud_policy.update_scan_policy(
        db=db,
        policy=policy,
        **body.model_dump(exclude_unset=True),
    )
    return updated


@router.delete("/{policy_id}", status_code=204)
def delete_policy(
    policy_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """删除扫描策略"""
    policy = crud_policy.get_scan_policy(db=db, policy_id=policy_id)
    if not policy or policy.project_id != project.id:
        raise HTTPException(status_code=404, detail="Policy not found")
    crud_policy.delete_scan_policy(db=db, policy=policy)
    return None
