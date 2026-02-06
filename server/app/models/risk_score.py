"""
Risk Score Models - Asset risk scoring and risk factors

This module defines models for tracking asset risk scores and
configurable risk factors used in the scoring algorithm.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from server.app.db.session import Base


class RiskFactor(Base):
    """风险因子定义"""

    __tablename__ = "risk_factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Float, nullable=False, default=1.0)  # 权重 0.0-1.0
    max_score = Column(Integer, nullable=False, default=100)  # 最大分值
    factor_type = Column(String(50), nullable=False)  # vulnerability, exposure, config, etc.
    calculation_rule = Column(JSONB, nullable=False, default=dict)  # 计算规则
    is_system = Column(Boolean, nullable=False, default=False)  # 系统预设因子
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AssetRiskScore(Base):
    """资产风险评分记录"""

    __tablename__ = "asset_risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(String(50), nullable=False)  # subdomain, ip_address, web_asset, etc.
    asset_id = Column(UUID(as_uuid=True), nullable=False)  # 关联资产ID
    
    # 评分结果
    total_score = Column(Float, nullable=False, default=0.0)  # 综合风险评分 0-100
    severity_level = Column(String(20), nullable=False, default="low")  # critical, high, medium, low, info
    
    # 评分详情
    factor_scores = Column(JSONB, nullable=False, default=dict)  # {factor_id: {score, details}}
    risk_summary = Column(JSONB, nullable=False, default=dict)  # 风险摘要
    
    # 时间戳
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 评分过期时间
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
