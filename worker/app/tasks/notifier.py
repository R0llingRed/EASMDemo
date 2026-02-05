"""
Notifier - Celery tasks for sending notifications through various channels

This module handles sending notifications via Email, Webhook, DingTalk,
Feishu (Lark), and WeChat Work.

Security features:
- SSRF protection for webhook URLs
- Sensitive config fetched from DB (not passed in task args)
- HTTP client connection pooling
"""

import ipaddress
import logging
import socket
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from server.app.crud import alert as crud_alert
from server.app.db.session import SessionLocal
from worker.app.celery_app import celery_app

logger = logging.getLogger(__name__)

# HTTP 客户端连接池（复用连接）
_http_client: Optional[httpx.Client] = None


def get_http_client() -> httpx.Client:
    """获取共享的 HTTP 客户端"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=10, follow_redirects=False)
    return _http_client


def get_db() -> Session:
    """获取数据库会话"""
    return SessionLocal()


def is_safe_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    检查 URL 是否安全（防止 SSRF 攻击）
    
    Returns:
        (is_safe, error_message)
    """
    try:
        parsed = urlparse(url)
        
        # 检查协议
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported protocol: {parsed.scheme}"
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname"
        
        # 检查常见内网域名
        blocked_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
        blocked_suffixes = [".local", ".internal", ".localhost"]
        
        if hostname.lower() in blocked_hosts:
            return False, f"Blocked host: {hostname}"
        
        if any(hostname.lower().endswith(suffix) for suffix in blocked_suffixes):
            return False, f"Blocked domain suffix: {hostname}"
        
        # 尝试解析 IP 地址
        try:
            # 解析域名获取 IP
            ips = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
            for family, _, _, _, addr in ips:
                ip_str = addr[0]
                try:
                    ip = ipaddress.ip_address(ip_str)
                    if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                        return False, f"Private/internal IP detected: {ip_str}"
                except ValueError:
                    continue
        except socket.gaierror:
            # 无法解析域名，允许继续（可能是外网地址）
            pass
        
        return True, None
        
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


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
    notification_data: Dict[str, Any],
    alert_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    发送通知到指定渠道
    
    安全改进：从数据库获取渠道配置，避免敏感信息通过任务参数传递
    
    Args:
        channel_id: 渠道ID
        notification_data: 通知数据
        alert_id: 关联的告警ID
    """
    db = None
    try:
        db = get_db()
        
        # 从数据库获取渠道配置（安全：不通过任务参数传递敏感信息）
        channel = crud_alert.get_notification_channel(db=db, channel_id=UUID(channel_id))
        if not channel:
            return {"status": "error", "message": "Channel not found"}
        
        if not channel.enabled:
            return {"status": "skipped", "message": "Channel is disabled"}
        
        channel_type = channel.channel_type
        config = channel.config
        
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
        if db:
            db.close()


@celery_app.task(bind=True, name="worker.app.tasks.notifier.test_channel")
def test_channel(
    self,
    channel_id: str,
) -> Dict[str, Any]:
    """
    测试通知渠道
    
    安全改进：从数据库获取渠道配置
    """
    db = None
    try:
        db = get_db()
        
        # 从数据库获取渠道配置
        channel = crud_alert.get_notification_channel(db=db, channel_id=UUID(channel_id))
        if not channel:
            return {"status": "error", "message": "Channel not found"}
        
        channel_type = channel.channel_type
        config = channel.config
        
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
        if db:
            db.close()


def send_email_notification(
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    发送邮件通知
    
    TODO: 实现真实的 SMTP 发送逻辑
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = config.get("smtp_host")
        smtp_port = config.get("smtp_port", 587)
        username = config.get("username")
        password = config.get("password")
        recipients = config.get("recipients", [])
        sender = config.get("sender") or username
        
        if not smtp_host or not recipients:
            return False, "Missing SMTP configuration (smtp_host, recipients)"
        
        # 构建邮件
        message = format_notification_message(notification_data)
        
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = notification_data.get("title", "EASM Alert")
        msg.attach(MIMEText(message, "plain", "utf-8"))
        
        # 发送邮件
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.sendmail(sender, recipients, msg.as_string())
        
        logger.info(f"Email notification sent to {recipients}")
        return True, None
        
    except Exception as e:
        logger.exception(f"Failed to send email: {e}")
        return False, str(e)


def send_webhook_notification(
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """发送 Webhook 通知（含 SSRF 防护）"""
    try:
        url = config.get("url") or config.get("webhook_url")
        if not url:
            return False, "Missing webhook URL"
        
        # SSRF 防护：检查 URL 是否安全
        is_safe, safety_error = is_safe_url(url)
        if not is_safe:
            logger.warning(f"SSRF protection blocked URL: {url} - {safety_error}")
            return False, f"URL blocked for security: {safety_error}"
        
        headers = dict(config.get("headers", {}))
        headers.setdefault("Content-Type", "application/json")
        
        payload = {
            "title": notification_data.get("title"),
            "message": notification_data.get("message"),
            "severity": notification_data.get("severity"),
            "target_type": notification_data.get("target_type"),
            "created_at": notification_data.get("created_at"),
            "details": notification_data.get("details", {}),
        }
        
        client = get_http_client()
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def send_dingtalk_notification(
    config: Dict[str, Any],
    notification_data: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """发送钉钉通知（含 SSRF 防护）"""
    try:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return False, "Missing DingTalk webhook URL"
        
        # SSRF 防护：检查 URL（钉钉官方域名应该通过）
        is_safe, safety_error = is_safe_url(webhook_url)
        if not is_safe:
            logger.warning(f"SSRF protection blocked URL: {webhook_url} - {safety_error}")
            return False, f"URL blocked for security: {safety_error}"
        
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
        
        client = get_http_client()
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
) -> Tuple[bool, Optional[str]]:
    """发送飞书通知（含 SSRF 防护）"""
    try:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return False, "Missing Feishu webhook URL"
        
        # SSRF 防护
        is_safe, safety_error = is_safe_url(webhook_url)
        if not is_safe:
            logger.warning(f"SSRF protection blocked URL: {webhook_url} - {safety_error}")
            return False, f"URL blocked for security: {safety_error}"
        
        message = format_notification_message(notification_data)
        
        payload = {
            "msg_type": "text",
            "content": {"text": message},
        }
        
        client = get_http_client()
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
) -> Tuple[bool, Optional[str]]:
    """发送企业微信通知（含 SSRF 防护）"""
    try:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return False, "Missing WeChat Work webhook URL"
        
        # SSRF 防护
        is_safe, safety_error = is_safe_url(webhook_url)
        if not is_safe:
            logger.warning(f"SSRF protection blocked URL: {webhook_url} - {safety_error}")
            return False, f"URL blocked for security: {safety_error}"
        
        message = format_notification_message(notification_data)
        
        payload = {
            "msgtype": "text",
            "text": {"content": message},
        }
        
        client = get_http_client()
        response = client.post(webhook_url, json=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("errcode") != 0:
            return False, result.get("errmsg", "WeChat Work API error")
        
        return True, None
        
    except Exception as e:
        return False, str(e)

