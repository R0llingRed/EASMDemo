"""
Alerter - Celery tasks for checking alert conditions and creating alerts

This module handles alert condition checking, alert creation with aggregation,
and triggering notification delivery.
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.crud import alert as crud_alert
from server.app.db.session import SessionLocal
from worker.app.celery_app import celery_app
from worker.app.tasks import notifier

logger = logging.getLogger(__name__)

# 严重度优先级
SEVERITY_PRIORITY = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
}


def get_db() -> Session:
    """获取数据库会话"""
    return SessionLocal()


def generate_aggregation_key(
    project_id: str,
    target_type: str,
    severity: str,
    alert_type: str,
) -> str:
    """生成告警聚合键（使用 SHA256）"""
    key = f"{project_id}:{target_type}:{severity}:{alert_type}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def check_severity_threshold(severity: str, threshold: str) -> bool:
    """检查严重度是否达到阈值"""
    return SEVERITY_PRIORITY.get(severity, 0) >= SEVERITY_PRIORITY.get(threshold, 0)


@celery_app.task(bind=True, name="worker.app.tasks.alerter.check_vulnerability_alert")
def check_vulnerability_alert(
    self,
    project_id: str,
    vulnerability_id: str,
    severity: str,
    title: str,
    details: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    检查漏洞是否需要触发告警
    
    Args:
        project_id: 项目ID
        vulnerability_id: 漏洞ID
        severity: 严重度
        title: 漏洞标题
        details: 详细信息
    """
    db = get_db()
    try:
        project_uuid = UUID(project_id)
        vuln_uuid = UUID(vulnerability_id)
        
        # 获取启用的告警策略
        policies = crud_alert.list_alert_policies(
            db=db,
            project_id=project_uuid,
            enabled=True,
        )
        
        if not policies:
            return {"status": "ok", "message": "No active alert policies"}
        
        alerts_created = []
        
        for policy in policies:
            # 检查严重度阈值
            if not check_severity_threshold(severity, policy.severity_threshold):
                continue
            
            # 检查每小时告警限制
            recent_count = crud_alert.count_recent_alerts(
                db=db,
                project_id=project_uuid,
                policy_id=policy.id,
                hours=1,
            )
            if recent_count >= policy.max_alerts_per_hour:
                logger.info(f"Policy {policy.id} reached hourly limit")
                continue
            
            # 生成聚合键
            aggregation_key = generate_aggregation_key(
                project_id, "vulnerability", severity, "vuln_found"
            )
            
            # 检查冷却期
            if crud_alert.check_cooldown(
                db=db,
                project_id=project_uuid,
                aggregation_key=aggregation_key,
                cooldown_minutes=policy.cooldown_minutes,
            ):
                logger.info(f"Alert in cooldown period for key {aggregation_key}")
                continue
            
            # 检查是否可聚合
            existing = crud_alert.find_aggregatable_alert(
                db=db,
                project_id=project_uuid,
                aggregation_key=aggregation_key,
                window_minutes=policy.aggregation_window,
            )
            
            if existing:
                # 增加聚合计数
                crud_alert.increment_aggregated_count(db=db, record=existing)
                alerts_created.append({
                    "alert_id": str(existing.id),
                    "aggregated": True,
                    "count": existing.aggregated_count,
                })
            else:
                # 创建新告警
                message = f"发现 {severity.upper()} 级别漏洞: {title}"
                
                record = crud_alert.create_alert_record(
                    db=db,
                    project_id=project_uuid,
                    policy_id=policy.id,
                    target_type="vulnerability",
                    target_id=vuln_uuid,
                    title=f"[{severity.upper()}] {title}",
                    message=message,
                    severity=severity,
                    details=details or {},
                    aggregation_key=aggregation_key,
                )
                
                alerts_created.append({
                    "alert_id": str(record.id),
                    "aggregated": False,
                })
                
                # 触发通知发送
                if policy.channel_ids:
                    send_alert_notifications.delay(
                        alert_id=str(record.id),
                        channel_ids=policy.channel_ids,
                    )
        
        return {
            "status": "ok",
            "alerts_created": len(alerts_created),
            "alerts": alerts_created,
        }
        
    except Exception as e:
        logger.exception(f"Error checking vulnerability alert: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="worker.app.tasks.alerter.check_risk_score_alert")
def check_risk_score_alert(
    self,
    project_id: str,
    asset_type: str,
    asset_id: str,
    risk_score: float,
    severity_level: str,
) -> Dict[str, Any]:
    """
    检查风险评分是否需要触发告警
    """
    db = get_db()
    try:
        project_uuid = UUID(project_id)
        asset_uuid = UUID(asset_id)
        
        policies = crud_alert.list_alert_policies(
            db=db,
            project_id=project_uuid,
            enabled=True,
        )
        
        if not policies:
            return {"status": "ok", "message": "No active alert policies"}
        
        alerts_created = []
        
        for policy in policies:
            if not check_severity_threshold(severity_level, policy.severity_threshold):
                continue
            
            # 检查条件
            conditions = policy.conditions or {}
            min_score = conditions.get("min_risk_score", 0)
            if risk_score < min_score:
                continue
            
            aggregation_key = generate_aggregation_key(
                project_id, asset_type, severity_level, "high_risk"
            )
            
            if crud_alert.check_cooldown(
                db=db,
                project_id=project_uuid,
                aggregation_key=aggregation_key,
                cooldown_minutes=policy.cooldown_minutes,
            ):
                continue
            
            message = f"资产风险评分过高: {risk_score:.1f} ({severity_level.upper()})"
            
            record = crud_alert.create_alert_record(
                db=db,
                project_id=project_uuid,
                policy_id=policy.id,
                target_type=asset_type,
                target_id=asset_uuid,
                title=f"[{severity_level.upper()}] 高风险资产告警",
                message=message,
                severity=severity_level,
                details={"risk_score": risk_score, "asset_type": asset_type},
                aggregation_key=aggregation_key,
            )
            
            alerts_created.append({"alert_id": str(record.id)})
            
            if policy.channel_ids:
                send_alert_notifications.delay(
                    alert_id=str(record.id),
                    channel_ids=policy.channel_ids,
                )
        
        return {"status": "ok", "alerts_created": len(alerts_created)}
        
    except Exception as e:
        logger.exception(f"Error checking risk score alert: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="worker.app.tasks.alerter.send_alert_notifications")
def send_alert_notifications(
    self,
    alert_id: str,
    channel_ids: List[str],
) -> Dict[str, Any]:
    """
    发送告警通知到指定渠道
    """
    db = None
    try:
        db = get_db()
        alert_uuid = UUID(alert_id)
        record = crud_alert.get_alert_record(db=db, record_id=alert_uuid)
        
        if not record:
            return {"status": "error", "message": "Alert record not found"}
        
        notification_data = {
            "title": record.title,
            "message": record.message,
            "severity": record.severity,
            "target_type": record.target_type,
            "created_at": record.created_at.isoformat(),
            "details": record.details,
        }
        
        results = []
        for channel_id in channel_ids:
            channel = crud_alert.get_notification_channel(db=db, channel_id=UUID(channel_id))
            if not channel or not channel.enabled:
                continue
            
            # 调用通知任务（安全：不传递敏感配置，由 worker 从 DB 获取）
            notifier.send_notification.delay(
                channel_id=channel_id,
                notification_data=notification_data,
                alert_id=alert_id,
            )
            results.append({"channel_id": channel_id, "queued": True})
        
        # 更新告警状态
        crud_alert.update_alert_status(db=db, record=record, status="sent")
        
        return {"status": "ok", "notifications_queued": len(results)}
        
    except Exception as e:
        logger.exception(f"Error sending alert notifications: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if db:
            db.close()

