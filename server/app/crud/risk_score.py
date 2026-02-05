"""
Risk Score CRUD Operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.models.risk_score import AssetRiskScore, RiskFactor


# Risk Factor CRUD
def create_risk_factor(
    db: Session,
    project_id: Optional[UUID],
    name: str,
    factor_type: str,
    weight: float = 1.0,
    max_score: int = 100,
    description: Optional[str] = None,
    calculation_rule: Optional[dict] = None,
    is_system: bool = False,
    enabled: bool = True,
) -> RiskFactor:
    """创建风险因子"""
    factor = RiskFactor(
        project_id=project_id,
        name=name,
        description=description,
        weight=weight,
        max_score=max_score,
        factor_type=factor_type,
        calculation_rule=calculation_rule or {},
        is_system=is_system,
        enabled=enabled,
    )
    db.add(factor)
    db.commit()
    db.refresh(factor)
    return factor


def get_risk_factor(db: Session, factor_id: UUID) -> Optional[RiskFactor]:
    """获取风险因子"""
    return db.query(RiskFactor).filter(RiskFactor.id == factor_id).first()


def list_risk_factors(
    db: Session,
    project_id: Optional[UUID] = None,
    factor_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    include_system: bool = True,
) -> List[RiskFactor]:
    """列出风险因子"""
    query = db.query(RiskFactor)
    
    if project_id:
        if include_system:
            query = query.filter(
                (RiskFactor.project_id == project_id) | (RiskFactor.is_system == True)
            )
        else:
            query = query.filter(RiskFactor.project_id == project_id)
    elif include_system:
        query = query.filter(RiskFactor.is_system == True)
    
    if factor_type:
        query = query.filter(RiskFactor.factor_type == factor_type)
    if enabled is not None:
        query = query.filter(RiskFactor.enabled == enabled)
    
    return query.order_by(RiskFactor.weight.desc()).all()


def update_risk_factor(db: Session, factor: RiskFactor, **kwargs) -> RiskFactor:
    """更新风险因子"""
    for key, value in kwargs.items():
        if value is not None and hasattr(factor, key):
            setattr(factor, key, value)
    db.commit()
    db.refresh(factor)
    return factor


def delete_risk_factor(db: Session, factor: RiskFactor) -> None:
    """删除风险因子"""
    db.delete(factor)
    db.commit()


# Asset Risk Score CRUD
def create_or_update_risk_score(
    db: Session,
    project_id: UUID,
    asset_type: str,
    asset_id: UUID,
    total_score: float,
    severity_level: str,
    factor_scores: Dict[str, Any],
    risk_summary: Dict[str, Any],
    expires_at: Optional[datetime] = None,
) -> AssetRiskScore:
    """创建或更新资产风险评分"""
    # 查找现有评分
    existing = db.query(AssetRiskScore).filter(
        AssetRiskScore.project_id == project_id,
        AssetRiskScore.asset_type == asset_type,
        AssetRiskScore.asset_id == asset_id,
    ).first()
    
    if existing:
        existing.total_score = total_score
        existing.severity_level = severity_level
        existing.factor_scores = factor_scores
        existing.risk_summary = risk_summary
        existing.calculated_at = datetime.utcnow()
        existing.expires_at = expires_at
        db.commit()
        db.refresh(existing)
        return existing
    else:
        score = AssetRiskScore(
            project_id=project_id,
            asset_type=asset_type,
            asset_id=asset_id,
            total_score=total_score,
            severity_level=severity_level,
            factor_scores=factor_scores,
            risk_summary=risk_summary,
            calculated_at=datetime.utcnow(),
            expires_at=expires_at,
        )
        db.add(score)
        db.commit()
        db.refresh(score)
        return score


def get_risk_score(db: Session, score_id: UUID) -> Optional[AssetRiskScore]:
    """获取风险评分"""
    return db.query(AssetRiskScore).filter(AssetRiskScore.id == score_id).first()


def get_asset_risk_score(
    db: Session,
    project_id: UUID,
    asset_type: str,
    asset_id: UUID,
) -> Optional[AssetRiskScore]:
    """获取指定资产的风险评分"""
    return db.query(AssetRiskScore).filter(
        AssetRiskScore.project_id == project_id,
        AssetRiskScore.asset_type == asset_type,
        AssetRiskScore.asset_id == asset_id,
    ).first()


def list_risk_scores(
    db: Session,
    project_id: UUID,
    asset_type: Optional[str] = None,
    severity_level: Optional[str] = None,
    min_score: Optional[float] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[AssetRiskScore]:
    """列出风险评分"""
    query = db.query(AssetRiskScore).filter(AssetRiskScore.project_id == project_id)
    
    if asset_type:
        query = query.filter(AssetRiskScore.asset_type == asset_type)
    if severity_level:
        query = query.filter(AssetRiskScore.severity_level == severity_level)
    if min_score is not None:
        query = query.filter(AssetRiskScore.total_score >= min_score)
    
    return query.order_by(AssetRiskScore.total_score.desc()).offset(skip).limit(limit).all()


def count_risk_scores(
    db: Session,
    project_id: UUID,
    asset_type: Optional[str] = None,
    severity_level: Optional[str] = None,
    min_score: Optional[float] = None,
) -> int:
    """统计风险评分数量"""
    query = db.query(AssetRiskScore).filter(AssetRiskScore.project_id == project_id)
    
    if asset_type:
        query = query.filter(AssetRiskScore.asset_type == asset_type)
    if severity_level:
        query = query.filter(AssetRiskScore.severity_level == severity_level)
    if min_score is not None:
        query = query.filter(AssetRiskScore.total_score >= min_score)
    
    return query.count()


def get_risk_statistics(db: Session, project_id: UUID) -> Dict[str, Any]:
    """获取风险统计信息"""
    from sqlalchemy import func
    
    # 按严重度统计
    severity_counts = db.query(
        AssetRiskScore.severity_level,
        func.count(AssetRiskScore.id)
    ).filter(
        AssetRiskScore.project_id == project_id
    ).group_by(AssetRiskScore.severity_level).all()
    
    # 平均分
    avg_score = db.query(func.avg(AssetRiskScore.total_score)).filter(
        AssetRiskScore.project_id == project_id
    ).scalar() or 0.0
    
    return {
        "severity_distribution": {level: count for level, count in severity_counts},
        "average_score": round(float(avg_score), 2),
        "total_assets": sum(count for _, count in severity_counts),
    }
