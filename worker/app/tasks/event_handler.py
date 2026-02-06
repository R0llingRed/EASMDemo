"""
Event Handler - Celery task for processing events and triggering DAGs

This module handles event processing, trigger matching, and DAG execution initiation.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.crud import dag_execution as crud_execution
from server.app.crud import dag_template as crud_template
from server.app.crud import event_trigger as crud_trigger
from worker.app.celery_app import celery_app
from worker.app.tasks import dag_executor

logger = logging.getLogger(__name__)


def get_db() -> Session:
    """获取数据库会话"""
    from server.app.db.session import SessionLocal

    return SessionLocal()


def match_filter(filter_config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
    """
    检查事件数据是否匹配过滤条件

    过滤条件格式：
    - {"key": "value"} - 精确匹配
    - {"key": ["v1", "v2"]} - 值在列表中
    - {"key": {"$gt": 10}} - 比较操作（暂不实现）

    Args:
        filter_config: 过滤配置
        event_data: 事件数据

    Returns:
        是否匹配
    """
    if not filter_config:
        return True

    for key, expected in filter_config.items():
        actual = event_data.get(key)

        if isinstance(expected, list):
            # 列表匹配
            if actual not in expected:
                return False
        else:
            # 精确匹配
            if actual != expected:
                return False

    return True


def get_matching_triggers(
    db: Session,
    project_id: UUID,
    event_type: str,
    event_data: Dict[str, Any],
) -> List:
    """
    获取匹配的事件触发器

    Args:
        db: 数据库会话
        project_id: 项目ID
        event_type: 事件类型
        event_data: 事件数据

    Returns:
        匹配的触发器列表
    """
    triggers = crud_trigger.get_triggers_by_event_type(
        db=db,
        project_id=project_id,
        event_type=event_type,
    )

    matching = []
    for trigger in triggers:
        if match_filter(trigger.filter_config, event_data):
            matching.append(trigger)

    return matching


def _process_event_internal(
    project_id: str,
    event_type: str,
    event_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    处理事件 - 查找匹配的触发器并启动DAG（纯函数，可被任务和普通函数复用）

    Args:
        project_id: 项目ID
        event_type: 事件类型
        event_data: 事件数据

    Returns:
        处理结果
    """
    db = get_db()
    try:
        project_uuid = UUID(project_id)

        # 查找匹配的触发器
        matching_triggers = get_matching_triggers(
            db=db,
            project_id=project_uuid,
            event_type=event_type,
            event_data=event_data,
        )

        if not matching_triggers:
            logger.debug(f"No matching triggers for event {event_type} in project {project_id}")
            return {
                "status": "ok",
                "message": "No matching triggers",
                "event_type": event_type,
            }

        triggered_dags = []
        for trigger in matching_triggers:
            try:
                # 获取DAG模板
                template = crud_template.get_dag_template(db=db, template_id=trigger.dag_template_id)
                if not template or not template.enabled:
                    logger.warning(f"DAG template {trigger.dag_template_id} not found or disabled")
                    crud_trigger.increment_trigger_count(db=db, trigger=trigger, success=False)
                    continue

                # 初始化节点状态
                initial_node_states = {}
                for node in template.nodes:
                    node_id = node.get("id") if isinstance(node, dict) else node.id
                    initial_node_states[node_id] = "pending"

                # 安全合并配置：触发器配置优先于事件数据，防止恶意覆盖
                # 事件数据只允许白名单字段
                safe_event_keys = {"asset_id", "asset_type", "scan_task_id", "task_type", "severity", "target", "source"}
                filtered_event_data = {k: v for k, v in event_data.items() if k in safe_event_keys}
                input_config = {**filtered_event_data, **trigger.dag_config}

                # 创建DAG执行实例
                execution = crud_execution.create_dag_execution(
                    db=db,
                    project_id=project_uuid,
                    dag_template_id=template.id,
                    trigger_type="event",
                    trigger_event={
                        "event_type": event_type,
                        "trigger_id": str(trigger.id),
                        "trigger_name": trigger.name,
                        "event_data": event_data,  # 保留完整事件数据用于审计
                    },
                    input_config=input_config,
                    initial_node_states=initial_node_states,
                )

                # 更新状态为运行中
                crud_execution.update_execution_status(db=db, execution=execution, status="running")

                # 异步启动DAG执行
                dag_executor.execute_dag.delay(str(execution.id))

                # 更新触发计数
                crud_trigger.increment_trigger_count(db=db, trigger=trigger, success=True)

                triggered_dags.append({
                    "trigger_id": str(trigger.id),
                    "trigger_name": trigger.name,
                    "execution_id": str(execution.id),
                    "dag_template_id": str(template.id),
                })

                logger.info(
                    f"Event {event_type} triggered DAG {template.name} "
                    f"(execution_id={execution.id})"
                )

            except Exception as e:
                logger.exception(f"Error processing trigger {trigger.id}: {e}")
                crud_trigger.increment_trigger_count(db=db, trigger=trigger, success=False)

        return {
            "status": "ok",
            "event_type": event_type,
            "triggered_count": len(triggered_dags),
            "triggered_dags": triggered_dags,
        }

    except Exception as e:
        logger.exception(f"Event processing error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="worker.app.tasks.event_handler.process_event")
def process_event(
    self,
    project_id: str,
    event_type: str,
    event_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Celery task wrapper for event processing."""
    return _process_event_internal(
        project_id=project_id,
        event_type=event_type,
        event_data=event_data,
    )


@celery_app.task(bind=True, name="worker.app.tasks.event_handler.emit_asset_event")
def emit_asset_event(
    self,
    project_id: str,
    event_type: str,
    asset_type: str,
    asset_id: str,
    asset_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    发送资产相关事件

    Args:
        project_id: 项目ID
        event_type: 事件类型
        asset_type: 资产类型 (subdomain, ip, url, etc.)
        asset_id: 资产ID
        asset_data: 资产数据

    Returns:
        处理结果
    """
    event_data = {
        "asset_type": asset_type,
        "asset_id": asset_id,
        **(asset_data or {}),
    }

    return _process_event_internal(
        project_id=project_id,
        event_type=event_type,
        event_data=event_data,
    )


@celery_app.task(bind=True, name="worker.app.tasks.event_handler.emit_scan_event")
def emit_scan_event(
    self,
    project_id: str,
    event_type: str,
    scan_task_id: str,
    task_type: str,
    result_summary: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    发送扫描相关事件

    Args:
        project_id: 项目ID
        event_type: 事件类型
        scan_task_id: 扫描任务ID
        task_type: 任务类型
        result_summary: 结果摘要

    Returns:
        处理结果
    """
    event_data = {
        "scan_task_id": scan_task_id,
        "task_type": task_type,
        **(result_summary or {}),
    }

    return _process_event_internal(
        project_id=project_id,
        event_type=event_type,
        event_data=event_data,
    )
