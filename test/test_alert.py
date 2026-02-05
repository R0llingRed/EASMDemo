"""
Unit tests for Alert functionality
"""

import pytest
from datetime import datetime
from uuid import uuid4

from server.app.schemas.alert import (
    AlertPolicyCreate,
    AlertPolicyUpdate,
    AlertRecordOut,
    AlertAcknowledgeRequest,
    AlertResolveRequest,
    NotificationChannelCreate,
    NotificationChannelUpdate,
    AlertSeverity,
    AlertStatus,
    ChannelType,
)


class TestNotificationChannelSchemas:
    """通知渠道 Schema 测试"""

    def test_create_webhook_channel(self):
        """测试创建 Webhook 渠道"""
        data = NotificationChannelCreate(
            name="Alert Webhook",
            description="Production alerts",
            channel_type=ChannelType.webhook,
            config={"url": "https://example.com/webhook", "secret": "abc123"},
            enabled=True,
        )
        assert data.name == "Alert Webhook"
        assert data.channel_type == ChannelType.webhook
        assert data.config["url"] == "https://example.com/webhook"

    def test_create_dingtalk_channel(self):
        """测试创建钉钉渠道"""
        data = NotificationChannelCreate(
            name="DingTalk Alert",
            channel_type=ChannelType.dingtalk,
            config={
                "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
                "at_all": False,
            },
        )
        assert data.channel_type == ChannelType.dingtalk

    def test_create_feishu_channel(self):
        """测试创建飞书渠道"""
        data = NotificationChannelCreate(
            name="Feishu Alert",
            channel_type=ChannelType.feishu,
            config={"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"},
        )
        assert data.channel_type == ChannelType.feishu

    def test_create_wechat_channel(self):
        """测试创建企业微信渠道"""
        data = NotificationChannelCreate(
            name="WeChat Work Alert",
            channel_type=ChannelType.wechat,
            config={"webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"},
        )
        assert data.channel_type == ChannelType.wechat

    def test_create_email_channel(self):
        """测试创建邮件渠道"""
        data = NotificationChannelCreate(
            name="Email Alert",
            channel_type=ChannelType.email,
            config={
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "username": "alert@example.com",
                "password": "secret",
                "recipients": ["admin@example.com"],
            },
        )
        assert data.channel_type == ChannelType.email

    def test_update_channel_partial(self):
        """测试部分更新"""
        data = NotificationChannelUpdate(enabled=False)
        assert data.enabled is False
        assert data.name is None
        assert data.config is None


class TestAlertPolicySchemas:
    """告警策略 Schema 测试"""

    def test_create_policy_basic(self):
        """测试创建基本策略"""
        channel_id = uuid4()
        data = AlertPolicyCreate(
            name="High Severity Alert",
            description="Alert on high and critical vulnerabilities",
            severity_threshold=AlertSeverity.high,
            channel_ids=[channel_id],
        )
        assert data.name == "High Severity Alert"
        assert data.severity_threshold == AlertSeverity.high
        assert len(data.channel_ids) == 1

    def test_create_policy_with_conditions(self):
        """测试创建带条件的策略"""
        data = AlertPolicyCreate(
            name="Risk Score Alert",
            conditions={"min_risk_score": 70, "asset_types": ["subdomain", "ip_address"]},
            severity_threshold=AlertSeverity.medium,
            channel_ids=[],
        )
        assert data.conditions["min_risk_score"] == 70

    def test_create_policy_defaults(self):
        """测试策略默认值"""
        data = AlertPolicyCreate(name="Test Policy")
        assert data.severity_threshold == AlertSeverity.high
        assert data.cooldown_minutes == 60
        assert data.aggregation_window == 5
        assert data.max_alerts_per_hour == 10
        assert data.enabled is True

    def test_policy_cooldown_validation(self):
        """测试冷却时间验证"""
        with pytest.raises(ValueError):
            AlertPolicyCreate(
                name="Test",
                cooldown_minutes=1500,  # 超出最大值 1440
            )

    def test_policy_max_alerts_validation(self):
        """测试每小时最大告警数验证"""
        with pytest.raises(ValueError):
            AlertPolicyCreate(
                name="Test",
                max_alerts_per_hour=0,  # 小于最小值 1
            )

    def test_update_policy_partial(self):
        """测试部分更新策略"""
        data = AlertPolicyUpdate(
            severity_threshold=AlertSeverity.critical,
            cooldown_minutes=120,
        )
        assert data.severity_threshold == AlertSeverity.critical
        assert data.cooldown_minutes == 120
        assert data.name is None


class TestAlertRecordSchemas:
    """告警记录 Schema 测试"""

    def test_acknowledge_request(self):
        """测试确认告警请求"""
        data = AlertAcknowledgeRequest(
            acknowledged_by="admin@example.com",
            notes="Investigating issue",
        )
        assert data.acknowledged_by == "admin@example.com"
        assert data.notes == "Investigating issue"

    def test_acknowledge_request_required_field(self):
        """测试确认请求必填字段"""
        with pytest.raises(ValueError):
            AlertAcknowledgeRequest(acknowledged_by="")

    def test_resolve_request(self):
        """测试解决告警请求"""
        data = AlertResolveRequest(resolution_notes="Fixed by patching")
        assert data.resolution_notes == "Fixed by patching"

    def test_resolve_request_optional_notes(self):
        """测试解决请求可选字段"""
        data = AlertResolveRequest()
        assert data.resolution_notes is None


class TestAlertEnums:
    """告警枚举测试"""

    def test_alert_severity_values(self):
        """测试告警严重度值"""
        assert AlertSeverity.critical.value == "critical"
        assert AlertSeverity.high.value == "high"
        assert AlertSeverity.medium.value == "medium"
        assert AlertSeverity.low.value == "low"
        assert AlertSeverity.info.value == "info"

    def test_alert_status_values(self):
        """测试告警状态值"""
        assert AlertStatus.pending.value == "pending"
        assert AlertStatus.sent.value == "sent"
        assert AlertStatus.acknowledged.value == "acknowledged"
        assert AlertStatus.resolved.value == "resolved"

    def test_channel_type_values(self):
        """测试渠道类型值"""
        assert ChannelType.email.value == "email"
        assert ChannelType.webhook.value == "webhook"
        assert ChannelType.dingtalk.value == "dingtalk"
        assert ChannelType.feishu.value == "feishu"
        assert ChannelType.wechat.value == "wechat"


class TestAlerterLogic:
    """告警逻辑测试"""

    # 严重度优先级（复制自 alerter）
    SEVERITY_PRIORITY = {
        "critical": 5,
        "high": 4,
        "medium": 3,
        "low": 2,
        "info": 1,
    }

    def check_severity_threshold(self, severity: str, threshold: str) -> bool:
        """检查严重度是否达到阈值"""
        return self.SEVERITY_PRIORITY.get(severity, 0) >= self.SEVERITY_PRIORITY.get(threshold, 0)

    def generate_aggregation_key(
        self, project_id: str, target_type: str, severity: str, alert_type: str
    ) -> str:
        """生成告警聚合键（使用 SHA256）"""
        import hashlib
        key = f"{project_id}:{target_type}:{severity}:{alert_type}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def test_severity_threshold_check_pass(self):
        """测试严重度阈值检查 - 通过"""
        assert self.check_severity_threshold("critical", "high") is True
        assert self.check_severity_threshold("high", "high") is True
        assert self.check_severity_threshold("high", "medium") is True

    def test_severity_threshold_check_fail(self):
        """测试严重度阈值检查 - 不通过"""
        assert self.check_severity_threshold("medium", "high") is False
        assert self.check_severity_threshold("low", "high") is False
        assert self.check_severity_threshold("info", "medium") is False

    def test_generate_aggregation_key(self):
        """测试聚合键生成"""
        key1 = self.generate_aggregation_key("proj1", "vulnerability", "high", "vuln_found")
        key2 = self.generate_aggregation_key("proj1", "vulnerability", "high", "vuln_found")
        key3 = self.generate_aggregation_key("proj2", "vulnerability", "high", "vuln_found")
        
        assert key1 == key2  # 相同参数产生相同键
        assert key1 != key3  # 不同项目产生不同键
        assert len(key1) == 16  # 键长度为16


class TestNotifierLogic:
    """通知器逻辑测试"""

    def format_notification_message(
        self, notification_data: dict, template: str = None
    ) -> str:
        """格式化通知消息"""
        if template:
            try:
                return template.format(**notification_data)
            except Exception:
                pass
        
        return (
            f"【{notification_data.get('severity', 'INFO').upper()}】{notification_data.get('title', 'Alert')}\n"
            f"消息: {notification_data.get('message', '')}\n"
            f"类型: {notification_data.get('target_type', '')}\n"
            f"时间: {notification_data.get('created_at', '')}"
        )

    def test_format_notification_message_default(self):
        """测试默认消息格式化"""
        data = {
            "title": "Test Alert",
            "message": "This is a test",
            "severity": "high",
            "target_type": "vulnerability",
            "created_at": "2026-02-05T12:00:00",
        }
        result = self.format_notification_message(data)
        assert "HIGH" in result
        assert "Test Alert" in result
        assert "This is a test" in result

    def test_format_notification_message_with_template(self):
        """测试自定义模板格式化"""
        data = {"title": "Alert", "severity": "critical"}
        template = "[{severity}] {title}"
        result = self.format_notification_message(data, template)
        assert result == "[critical] Alert"
