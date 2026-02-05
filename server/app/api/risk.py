"""
Risk Score API Routes
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import risk_score as crud_risk
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.risk_score import (
    RiskFactorCreate,
    RiskFactorOut,
    RiskFactorUpdate,
    AssetRiskScoreOut,
    RiskScoreCalculateRequest,
    SeverityLevel,
)
from worker.app.tasks import risk_calculator

router = APIRouter(prefix="/projects/{project_id}/risk", tags=["risk"])


# Risk Factors
@router.get("/factors", response_model=list[RiskFactorOut])
def list_risk_factors(
    factor_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    include_system: bool = True,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出风险因子"""
    factors = crud_risk.list_risk_factors(
        db=db,
        project_id=project.id,
        factor_type=factor_type,
        enabled=enabled,
        include_system=include_system,
    )
    return factors


@router.post("/factors", response_model=RiskFactorOut, status_code=201)
def create_risk_factor(
    body: RiskFactorCreate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """创建风险因子"""
    factor = crud_risk.create_risk_factor(
        db=db,
        project_id=project.id,
        name=body.name,
        description=body.description,
        weight=body.weight,
        max_score=body.max_score,
        factor_type=body.factor_type.value,
        calculation_rule=body.calculation_rule,
        enabled=body.enabled,
    )
    return factor


@router.get("/factors/{factor_id}", response_model=RiskFactorOut)
def get_risk_factor(
    factor_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取风险因子"""
    factor = crud_risk.get_risk_factor(db=db, factor_id=factor_id)
    if not factor:
        raise HTTPException(status_code=404, detail="Risk factor not found")
    if factor.project_id and factor.project_id != project.id:
        raise HTTPException(status_code=404, detail="Risk factor not found")
    return factor


@router.patch("/factors/{factor_id}", response_model=RiskFactorOut)
def update_risk_factor(
    factor_id: UUID,
    body: RiskFactorUpdate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """更新风险因子"""
    factor = crud_risk.get_risk_factor(db=db, factor_id=factor_id)
    if not factor:
        raise HTTPException(status_code=404, detail="Risk factor not found")
    if factor.project_id and factor.project_id != project.id:
        raise HTTPException(status_code=404, detail="Risk factor not found")
    if factor.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system risk factor")
    
    updated = crud_risk.update_risk_factor(db=db, factor=factor, **body.model_dump(exclude_unset=True))
    return updated


@router.delete("/factors/{factor_id}", status_code=204)
def delete_risk_factor(
    factor_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """删除风险因子"""
    factor = crud_risk.get_risk_factor(db=db, factor_id=factor_id)
    if not factor:
        raise HTTPException(status_code=404, detail="Risk factor not found")
    if factor.project_id and factor.project_id != project.id:
        raise HTTPException(status_code=404, detail="Risk factor not found")
    if factor.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system risk factor")
    crud_risk.delete_risk_factor(db=db, factor=factor)
    return None


# Risk Scores
@router.get("/scores", response_model=Page[AssetRiskScoreOut])
def list_risk_scores(
    asset_type: Optional[str] = None,
    severity_level: Optional[SeverityLevel] = None,
    min_score: Optional[float] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """列出资产风险评分"""
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    
    severity_str = severity_level.value if severity_level else None
    
    items = crud_risk.list_risk_scores(
        db=db,
        project_id=project.id,
        asset_type=asset_type,
        severity_level=severity_str,
        min_score=min_score,
        skip=skip,
        limit=limit,
    )
    total = crud_risk.count_risk_scores(
        db=db,
        project_id=project.id,
        asset_type=asset_type,
        severity_level=severity_str,
        min_score=min_score,
    )
    return Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/scores/{score_id}", response_model=AssetRiskScoreOut)
def get_risk_score(
    score_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取资产风险评分"""
    score = crud_risk.get_risk_score(db=db, score_id=score_id)
    if not score or score.project_id != project.id:
        raise HTTPException(status_code=404, detail="Risk score not found")
    return score


@router.post("/scores/calculate", status_code=202)
def trigger_risk_calculation(
    body: RiskScoreCalculateRequest,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """触发风险评分计算"""
    # 异步计算
    risk_calculator.calculate_project_risks.delay(
        project_id=str(project.id),
        asset_type=body.asset_type,
        asset_ids=[str(aid) for aid in body.asset_ids] if body.asset_ids else None,
        force_recalculate=body.force_recalculate,
    )
    return {"message": "Risk calculation started", "project_id": str(project.id)}


@router.get("/statistics")
def get_risk_statistics(
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """获取风险统计信息"""
    stats = crud_risk.get_risk_statistics(db=db, project_id=project.id)
    return stats
