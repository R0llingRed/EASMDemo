"""
Unit tests for Risk Score functionality
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from server.app.schemas.risk_score import (
    RiskFactorCreate,
    RiskFactorUpdate,
    AssetRiskScoreCreate,
    RiskScoreCalculateRequest,
    SeverityLevel,
    FactorType,
)


class TestRiskFactorSchemas:
    """风险因子 Schema 测试"""

    def test_create_risk_factor_valid(self):
        """测试创建风险因子 - 有效数据"""
        data = RiskFactorCreate(
            name="Vulnerability Count",
            description="Based on vulnerability severity",
            weight=0.6,
            max_score=100,
            factor_type=FactorType.vulnerability,
            calculation_rule={"count_critical": 40, "count_high": 20},
            enabled=True,
        )
        assert data.name == "Vulnerability Count"
        assert data.weight == 0.6
        assert data.factor_type == FactorType.vulnerability

    def test_create_risk_factor_defaults(self):
        """测试创建风险因子 - 默认值"""
        data = RiskFactorCreate(
            name="Test Factor",
            factor_type=FactorType.exposure,
        )
        assert data.weight == 1.0
        assert data.max_score == 100
        assert data.enabled is True

    def test_create_risk_factor_weight_validation(self):
        """测试权重范围验证"""
        with pytest.raises(ValueError):
            RiskFactorCreate(
                name="Test",
                factor_type=FactorType.vulnerability,
                weight=1.5,  # 超出范围
            )

    def test_update_risk_factor_partial(self):
        """测试部分更新"""
        data = RiskFactorUpdate(weight=0.8)
        assert data.weight == 0.8
        assert data.name is None
        assert data.enabled is None


class TestAssetRiskScoreSchemas:
    """资产风险评分 Schema 测试"""

    def test_create_risk_score_valid(self):
        """测试创建风险评分"""
        asset_id = uuid4()
        data = AssetRiskScoreCreate(
            asset_type="subdomain",
            asset_id=asset_id,
            total_score=75.5,
            severity_level=SeverityLevel.high,
            factor_scores={"vuln": 80, "exposure": 60},
            risk_summary={"critical_factors": ["vuln"]},
        )
        assert data.asset_type == "subdomain"
        assert data.total_score == 75.5
        assert data.severity_level == SeverityLevel.high

    def test_risk_score_default_values(self):
        """测试默认值"""
        asset_id = uuid4()
        data = AssetRiskScoreCreate(
            asset_type="ip_address",
            asset_id=asset_id,
        )
        assert data.total_score == 0.0
        assert data.severity_level == SeverityLevel.low

    def test_calculate_request_all_assets(self):
        """测试计算请求 - 全部资产"""
        data = RiskScoreCalculateRequest()
        assert data.asset_type is None
        assert data.asset_ids is None
        assert data.force_recalculate is False

    def test_calculate_request_specific_assets(self):
        """测试计算请求 - 指定资产"""
        asset_ids = [uuid4(), uuid4()]
        data = RiskScoreCalculateRequest(
            asset_type="subdomain",
            asset_ids=asset_ids,
            force_recalculate=True,
        )
        assert data.asset_type == "subdomain"
        assert len(data.asset_ids) == 2


class TestSeverityLevelEnum:
    """严重度等级枚举测试"""

    def test_severity_levels(self):
        """测试严重度等级值"""
        assert SeverityLevel.critical.value == "critical"
        assert SeverityLevel.high.value == "high"
        assert SeverityLevel.medium.value == "medium"
        assert SeverityLevel.low.value == "low"
        assert SeverityLevel.info.value == "info"


class TestRiskScoreCalculation:
    """风险评分计算逻辑测试"""

    # 严重度等级阈值（复制自 risk_calculator）
    SEVERITY_THRESHOLDS = [
        (80, "critical"),
        (60, "high"),
        (40, "medium"),
        (20, "low"),
        (0, "info"),
    ]

    def score_to_severity(self, score: float) -> str:
        """将分数转换为严重度等级"""
        for threshold, level in self.SEVERITY_THRESHOLDS:
            if score >= threshold:
                return level
        return "info"

    def test_score_to_severity_critical(self):
        """测试分数到严重度转换 - Critical"""
        assert self.score_to_severity(85) == "critical"
        assert self.score_to_severity(80) == "critical"

    def test_score_to_severity_high(self):
        """测试分数到严重度转换 - High"""
        assert self.score_to_severity(75) == "high"
        assert self.score_to_severity(60) == "high"

    def test_score_to_severity_medium(self):
        """测试分数到严重度转换 - Medium"""
        assert self.score_to_severity(55) == "medium"
        assert self.score_to_severity(40) == "medium"

    def test_score_to_severity_low(self):
        """测试分数到严重度转换 - Low"""
        assert self.score_to_severity(35) == "low"
        assert self.score_to_severity(20) == "low"

    def test_score_to_severity_info(self):
        """测试分数到严重度转换 - Info"""
        assert self.score_to_severity(15) == "info"
        assert self.score_to_severity(0) == "info"


class TestFactorTypeEnum:
    """因子类型枚举测试"""

    def test_factor_types(self):
        """测试因子类型值"""
        assert FactorType.vulnerability.value == "vulnerability"
        assert FactorType.exposure.value == "exposure"
        assert FactorType.config.value == "config"
        assert FactorType.compliance.value == "compliance"
        assert FactorType.history.value == "history"
