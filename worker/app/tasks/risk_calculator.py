"""
Risk Calculator - Celery tasks for calculating asset risk scores

This module handles the calculation of risk scores for assets based on
configurable risk factors (vulnerabilities, exposure, etc.).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from server.app.crud import risk_score as crud_risk
from server.app.db.session import SessionLocal
from worker.app.celery_app import celery_app

logger = logging.getLogger(__name__)

# 严重度分值映射
SEVERITY_SCORES = {
    "critical": 100,
    "high": 75,
    "medium": 50,
    "low": 25,
    "info": 10,
}

# 严重度等级阈值
SEVERITY_THRESHOLDS = [
    (80, "critical"),
    (60, "high"),
    (40, "medium"),
    (20, "low"),
    (0, "info"),
]


def get_db() -> Session:
    """获取数据库会话"""
    return SessionLocal()


def score_to_severity(score: float) -> str:
    """将分数转换为严重度等级"""
    for threshold, level in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return level
    return "info"


def calculate_vulnerability_factor(
    db: Session,
    project_id: UUID,
    asset_type: str,
    asset_id: UUID,
) -> Dict[str, Any]:
    """计算漏洞因子分数"""
    from server.app.models.vulnerability import Vulnerability
    
    # 查询资产相关漏洞（按资产类型和ID过滤）
    vulns = db.query(Vulnerability).filter(
        Vulnerability.project_id == project_id,
        Vulnerability.target_type == asset_type,
        Vulnerability.target_id == asset_id,
    ).all()
    
    # 统计各等级漏洞数量
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for vuln in vulns:
        severity = vuln.severity.lower() if vuln.severity else "info"
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    # 计算分数
    score = (
        severity_counts["critical"] * 40 +
        severity_counts["high"] * 20 +
        severity_counts["medium"] * 10 +
        severity_counts["low"] * 5
    )
    
    return {
        "score": min(score, 100),
        "details": {
            "vulnerability_counts": severity_counts,
            "total_vulnerabilities": sum(severity_counts.values()),
        }
    }


def calculate_exposure_factor(
    db: Session,
    project_id: UUID,
    asset_type: str,
    asset_id: UUID,
) -> Dict[str, Any]:
    """计算暴露因子分数"""
    from server.app.models.port import Port
    
    # 高风险端口
    high_risk_ports = {22, 23, 25, 445, 3389, 1433, 3306, 5432, 6379, 27017}
    
    # 查询开放端口（按资产过滤）
    query = db.query(Port).filter(Port.project_id == project_id)
    
    # 如果是 IP 地址资产，按 IP 过滤
    if asset_type == "ip_address":
        query = query.filter(Port.ip_address_id == asset_id)
    
    ports = query.all()
    
    open_ports = len(ports)
    high_risk_count = sum(1 for p in ports if p.port in high_risk_ports)
    
    # 计算分数
    score = min(open_ports * 2, 40) + high_risk_count * 10
    
    return {
        "score": min(score, 100),
        "details": {
            "open_ports": open_ports,
            "high_risk_ports": high_risk_count,
        }
    }


def calculate_asset_risk(
    project_id: UUID,
    asset_type: str,
    asset_id: UUID,
    factors: List[dict],
) -> Dict[str, Any]:
    """
    计算单个资产的风险评分
    
    Args:
        project_id: 项目ID
        asset_type: 资产类型
        asset_id: 资产ID
        factors: 风险因子列表
    """
    db = None
    try:
        db = get_db()
        factor_scores = {}
        total_weight = 0
        weighted_score = 0
        
        for factor in factors:
            if not factor.get("enabled", True):
                continue
            
            factor_id = str(factor.get("id", factor.get("name")))
            factor_type = factor.get("factor_type")
            weight = factor.get("weight", 1.0)
            
            # 根据因子类型计算分数
            if factor_type == "vulnerability":
                result = calculate_vulnerability_factor(db, project_id, asset_type, asset_id)
            elif factor_type == "exposure":
                result = calculate_exposure_factor(db, project_id, asset_type, asset_id)
            else:
                result = {"score": 0, "details": {}}
            
            factor_scores[factor_id] = {
                "score": result["score"],
                "weight": weight,
                "weighted_score": result["score"] * weight,
                "details": result.get("details", {}),
            }
            
            weighted_score += result["score"] * weight
            total_weight += weight
        
        # 计算综合分数
        total_score = weighted_score / total_weight if total_weight > 0 else 0
        severity_level = score_to_severity(total_score)
        
        # 生成风险摘要
        risk_summary = {
            "total_factors": len(factor_scores),
            "highest_factor": max(factor_scores.items(), key=lambda x: x[1]["score"])[0] if factor_scores else None,
        }
        
        # 保存评分
        crud_risk.create_or_update_risk_score(
            db=db,
            project_id=project_id,
            asset_type=asset_type,
            asset_id=asset_id,
            total_score=round(total_score, 2),
            severity_level=severity_level,
            factor_scores=factor_scores,
            risk_summary=risk_summary,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        
        return {
            "status": "ok",
            "asset_type": asset_type,
            "asset_id": str(asset_id),
            "total_score": round(total_score, 2),
            "severity_level": severity_level,
        }
        
    except Exception as e:
        logger.exception(f"Error calculating risk for asset {asset_id}: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if db:
            db.close()


@celery_app.task(bind=True, name="worker.app.tasks.risk_calculator.calculate_project_risks")
def calculate_project_risks(
    self,
    project_id: str,
    asset_type: Optional[str] = None,
    asset_ids: Optional[List[str]] = None,
    force_recalculate: bool = False,
) -> Dict[str, Any]:
    """
    计算项目所有资产的风险评分
    
    Args:
        project_id: 项目ID
        asset_type: 可选，指定资产类型
        asset_ids: 可选，指定资产ID列表
        force_recalculate: 强制重新计算
    """
    db = get_db()
    try:
        project_uuid = UUID(project_id)
        
        # 获取风险因子
        factors = crud_risk.list_risk_factors(
            db=db,
            project_id=project_uuid,
            enabled=True,
            include_system=True,
        )
        
        if not factors:
            # 使用默认因子
            factors = [
                {"id": "vulnerability", "name": "vulnerability", "factor_type": "vulnerability", "weight": 0.6, "enabled": True},
                {"id": "exposure", "name": "exposure", "factor_type": "exposure", "weight": 0.4, "enabled": True},
            ]
        else:
            factors = [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "factor_type": f.factor_type,
                    "weight": f.weight,
                    "enabled": f.enabled,
                }
                for f in factors
            ]
        
        # 获取资产列表
        assets = []
        
        if asset_ids:
            # 使用指定的资产ID
            for aid in asset_ids:
                assets.append({
                    "type": asset_type or "unknown",
                    "id": UUID(aid),
                })
        else:
            # 从各资产表获取
            from server.app.models.subdomain import Subdomain
            from server.app.models.ip_address import IPAddress
            from server.app.models.web_asset import WebAsset
            
            if not asset_type or asset_type == "subdomain":
                subdomains = db.query(Subdomain.id).filter(
                    Subdomain.project_id == project_uuid
                ).all()
                assets.extend([{"type": "subdomain", "id": s.id} for s in subdomains])
            
            if not asset_type or asset_type == "ip_address":
                ips = db.query(IPAddress.id).filter(
                    IPAddress.project_id == project_uuid
                ).all()
                assets.extend([{"type": "ip_address", "id": i.id} for i in ips])
            
            if not asset_type or asset_type == "web_asset":
                web_assets = db.query(WebAsset.id).filter(
                    WebAsset.project_id == project_uuid
                ).all()
                assets.extend([{"type": "web_asset", "id": w.id} for w in web_assets])
        
        db.close()
        
        # 计算每个资产的风险
        results = []
        for asset in assets[:1000]:  # 限制最大处理数量
            result = calculate_asset_risk(
                project_id=project_uuid,
                asset_type=asset["type"],
                asset_id=asset["id"],
                factors=factors,
            )
            results.append(result)
        
        return {
            "status": "ok",
            "project_id": project_id,
            "total_assets": len(assets),
            "calculated": len(results),
            "success": sum(1 for r in results if r.get("status") == "ok"),
        }
        
    except Exception as e:
        logger.exception(f"Error calculating project risks: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if db:
            try:
                db.close()
            except:
                pass
