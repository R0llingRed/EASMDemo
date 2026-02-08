from typing import List, Tuple
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from server.app.models.alert import AlertPolicy, AlertRecord, NotificationChannel
from server.app.models.api_endpoint import APIEndpoint
from server.app.models.api_risk_finding import APIRiskFinding
from server.app.models.asset_entity import AssetEntity
from server.app.models.dag_execution import DAGExecution
from server.app.models.dag_template import DAGTemplate
from server.app.models.event_trigger import EventTrigger
from server.app.models.ip_address import IPAddress
from server.app.models.js_asset import JSAsset
from server.app.models.port import Port
from server.app.models.project import Project
from server.app.models.risk_score import AssetRiskScore, RiskFactor
from server.app.models.scan_policy import ScanPolicy
from server.app.models.scan_task import ScanTask
from server.app.models.subdomain import Subdomain
from server.app.models.vulnerability import Vulnerability
from server.app.models.web_asset import WebAsset


def create_project(db: Session, name: str, description: str | None) -> Project:
    project = Project(name=name, description=description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id) -> Project | None:
    return db.get(Project, project_id)


def list_projects(db: Session, offset: int, limit: int) -> Tuple[int, List[Project]]:
    total = db.scalar(select(func.count()).select_from(Project)) or 0
    items = db.scalars(select(Project).offset(offset).limit(limit)).all()
    return total, items


def update_project(
    db: Session,
    project: Project,
    name: str | None = None,
    description: str | None = None,
) -> Project:
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: UUID) -> bool:
    project = db.get(Project, project_id)
    if not project:
        return False

    ip_subquery = select(IPAddress.id).where(IPAddress.project_id == project_id)

    # Remove dependency chains from leaf to root.
    db.execute(delete(APIRiskFinding).where(APIRiskFinding.project_id == project_id))
    db.execute(delete(APIEndpoint).where(APIEndpoint.project_id == project_id))
    db.execute(delete(JSAsset).where(JSAsset.project_id == project_id))
    db.execute(delete(WebAsset).where(WebAsset.project_id == project_id))
    db.execute(delete(Port).where(Port.ip_id.in_(ip_subquery)))
    db.execute(delete(IPAddress).where(IPAddress.project_id == project_id))
    db.execute(delete(Subdomain).where(Subdomain.project_id == project_id))

    db.execute(delete(Vulnerability).where(Vulnerability.project_id == project_id))
    db.execute(delete(ScanTask).where(ScanTask.project_id == project_id))
    db.execute(delete(ScanPolicy).where(ScanPolicy.project_id == project_id))
    db.execute(delete(AssetEntity).where(AssetEntity.project_id == project_id))

    db.execute(delete(AlertRecord).where(AlertRecord.project_id == project_id))
    db.execute(delete(AlertPolicy).where(AlertPolicy.project_id == project_id))
    db.execute(delete(NotificationChannel).where(NotificationChannel.project_id == project_id))
    db.execute(delete(AssetRiskScore).where(AssetRiskScore.project_id == project_id))
    db.execute(delete(RiskFactor).where(RiskFactor.project_id == project_id))

    db.execute(delete(DAGExecution).where(DAGExecution.project_id == project_id))
    db.execute(delete(EventTrigger).where(EventTrigger.project_id == project_id))
    db.execute(delete(DAGTemplate).where(DAGTemplate.project_id == project_id))

    db.execute(delete(Project).where(Project.id == project_id))
    db.commit()
    return True
