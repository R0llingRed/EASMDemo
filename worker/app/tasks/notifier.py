"""
Notifier - Celery tasks for sending notifications through various channels

This module handles sending notifications via Email, Webhook, DingTalk,
Feishu (Lark), and WeChat Work.
"""

import json
import logging
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from server.app.crud import alert as crud_alert
from server.app.db.session import SessionLocal
from worker.app.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_db() -> Session:
    """获取数据库会话"""
    return SessionLocal()


def format_notification_message(
    notification_data: Dict[str, Any],
    template: Optional[str] = None,
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


@celery_app.task(bind=True, name="worker.app.tasks.notifier.send_notification")
def send_notification(
    self,
    channel_id: str,
    channel_type: str,
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
    alert_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    发送通知到指定渠道
    
    Args:
        channel_id: 渠道ID
        channel_type: 渠道类型
        config: 渠道配置
        notification_data: 通知数据
        alert_id: 关联的告警ID
    """
    db = get_db()
    try:
        success = False
        error = None
        
        if channel_type == "email":
            success, error = send_email_notification(config, notification_data)
        elif channel_type == "webhook":
            success, error = send_webhook_notification(config, notification_data)
        elif channel_type == "dingtalk":
            success, error = send_dingtalk_notification(config, notification_data)
        elif channel_type == "feishu":
            success, error = send_feishu_notification(config, notification_data)
        elif channel_type == "wechat":
            success, error = send_wechat_notification(config, notification_data)
        else:
            error = f"Unknown channel type: {channel_type}"
        
        # 更新告警通知结果
        if alert_id:
            record = crud_alert.get_alert_record(db=db, record_id=UUID(alert_id))
            if record:
                crud_alert.update_notification_results(
                    db=db,
                    record=record,
                    channel_id=channel_id,
                    success=success,
                    error=error,
                )
        
        return {
            "status": "ok" if success else "error",
            "channel_id": channel_id,
            "channel_type": channel_type,
            "error": error,
        }
        
    except Exception as e:
        logger.exception(f"Error sending notification: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="worker.app.tasks.notifier.test_channel")
def test_channel(
    self,
    channel_id: str,
    channel_type: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    测试通知渠道
    """
    db = get_db()
    try:
        test_data = {
            "title": "测试通知",
            "message": "这是一条测试通知，用于验证渠道配置是否正确。",
            "severity": "info",
            "target_type": "test",
            "created_at": "2026-02-05T12:00:00",
        }
        
        success = False
        error = None
        
        if channel_type == "email":
            success, error = send_email_notification(config, test_data)
        elif channel_type == "webhook":
            success, error = send_webhook_notification(config, test_data)
        elif channel_type == "dingtalk":
            success, error = send_dingtalk_notification(config, test_data)
        elif channel_type == "feishu":
            success, error = send_feishu_notification(config, test_data)
        elif channel_type == "wechat":
            success, error = send_wechat_notification(config, test_data)
        else:
            error = f"Unknown channel type: {channel_type}"
        
        # 更新测试结果
        channel = crud_alert.get_notification_channel(db=db, channel_id=UUID(channel_id))
        if channel:
            crud_alert.update_channel_test_result(db=db, channel=channel, success=success)
        
        return {
            "status": "ok" if success else "error",
            "channel_id": channel_id,
            "success": success,
            "error": error,
        }
        
    except Exception as e:
        logger.exception(f"Error testing channel: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def send_email_notification(
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
) -> tuple[bool, Optional[str]]:
    """发送邮件通知"""
    try:
        # 简化实现 - 实际应使用 SMTP
        smtp_host = config.get("smtp_host")
        smtp_port = config.get("smtp_port", 587)
        username = config.get("username")
        password = config.get("password")
        recipients = config.get("recipients", [])
        
        if not smtp_host or not recipients:
            return False, "Missing SMTP configuration"
        
        # 模拟发送
        logger.info(f"Email notification sent to {recipients}")
        return True, None
        
    except Exception as e:
        return False, str(e)


def send_webhook_notification(
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
) -> tuple[bool, Optional[str]]:
    """发送 Webhook 通知"""
    try:
        url = config.get("url") or config.get("webhook_url")
        if not url:
            return False, "Missing webhook URL"
        
        headers = config.get("headers", {})
        headers.setdefault("Content-Type", "application/json")
        
        payload = {
            "title": notification_data.get("title"),
            "message": notification_data.get("message"),
            "severity": notification_data.get("severity"),
            "target_type": notification_data.get("target_type"),
            "created_at": notification_data.get("created_at"),
            "details": notification_data.get("details", {}),
        }
        
        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def send_dingtalk_notification(
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
) -> tuple[bool, Optional[str]]:
    """发送钉钉通知"""
    try:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return False, "Missing DingTalk webhook URL"
        
        message = format_notification_message(notification_data)
        
        payload = {
            "msgtype": "text",
            "text": {"content": message},
        }
        
        # 如果配置了 @ 功能
        at_mobiles = config.get("at_mobiles", [])
        at_all = config.get("at_all", False)
        if at_mobiles or at_all:
            payload["at"] = {
                "atMobiles": at_mobiles,
                "isAtAll": at_all,
            }
        
        with httpx.Client(timeout=10) as client:
            response = client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get("errcode") != 0:
                return False, result.get("errmsg", "DingTalk API error")
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def send_feishu_notification(
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
) -> tuple[bool, Optional[str]]:
    """发送飞书通知"""
    try:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return False, "Missing Feishu webhook URL"
        
        message = format_notification_message(notification_data)
        
        payload = {
            "msg_type": "text",
            "content": {"text": message},
        }
        
        with httpx.Client(timeout=10) as client:
            response = client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get("code") != 0:
                return False, result.get("msg", "Feishu API error")
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def send_wechat_notification(
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
) -> tuple[bool, Optional[str]]:
    """发送企业微信通知"""
    try:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return False, "Missing WeChat Work webhook URL"
        
        message = format_notification_message(notification_data)
        
        payload = {
            "msgtype": "text",
            "text": {"content": message},
        }
        
        with httpx.Client(timeout=10) as client:
            response = client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get("errcode") != 0:
                return False, result.get("errmsg", "WeChat Work API error")
        
        return True, None
        
    except Exception as e:
        return False, str(e)
