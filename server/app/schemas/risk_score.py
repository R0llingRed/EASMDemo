"""
Risk Score Schemas - Pydantic models for risk assessment
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class FactorType(str, Enum):
    vulnerability = "vulnerability"
    exposure = "exposure"
    config = "config"
    compliance = "compliance"
    history = "history"


# Risk Factor Schemas
class RiskFactorCreate(BaseModel):
    """创建风险因子"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    max_score: int = Field(default=100, ge=0, le=100)
    factor_type: FactorType
    calculation_rule: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class RiskFactorUpdate(BaseModel):
    """更新风险因子"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_score: Optional[int] = Field(None, ge=0, le=100)
    calculation_rule: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class RiskFactorOut(BaseModel):
    """风险因子输出"""
    id: UUID
    project_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    weight: float
    max_score: int
    factor_type: str
    calculation_rule: Dict[str, Any]
    is_system: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Asset Risk Score Schemas
class AssetRiskScoreCreate(BaseModel):
    """创建资产风险评分"""
    asset_type: str
    asset_id: UUID
    total_score: float = Field(default=0.0, ge=0.0, le=100.0)
    severity_level: SeverityLevel = SeverityLevel.low
    factor_scores: Dict[str, Any] = Field(default_factory=dict)
    risk_summary: Dict[str, Any] = Field(default_factory=dict)


class AssetRiskScoreOut(BaseModel):
    """资产风险评分输出"""
    id: UUID
    project_id: UUID
    asset_type: str
    asset_id: UUID
    total_score: float
    severity_level: str
    factor_scores: Dict[str, Any]
    risk_summary: Dict[str, Any]
    calculated_at: datetime
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskScoreCalculateRequest(BaseModel):
    """触发风险评分计算请求"""
    asset_type: Optional[str] = None  # 指定资产类型，None表示全部
    asset_ids: Optional[List[UUID]] = None  # 指定资产ID列表，None表示全部
    force_recalculate: bool = False  # 强制重新计算
