"""CRUD operations for API risk findings."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from server.app.models.api_risk_finding import APIRiskFinding


def _append_status_history(
    finding: APIRiskFinding,
    previous_status: str,
    new_status: str,
    updated_by: Optional[str],
    notes: Optional[str],
) -> None:
    history = list(finding.status_history or [])
    history.append(
        {
            "from": previous_status,
            "to": new_status,
            "by": updated_by,
            "notes": notes,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    finding.status_history = history


def create_or_update_api_risk_finding(
    db: Session,
    project_id: UUID,
    endpoint_id: Optional[UUID],
    rule_name: str,
    severity: str,
    title: str,
    description: Optional[str] = None,
    evidence: Optional[dict] = None,
    status: str = "open",
) -> APIRiskFinding:
    """Create or update a risk finding keyed by project + endpoint + rule."""
    finding = db.scalars(
        select(APIRiskFinding).where(
            APIRiskFinding.project_id == project_id,
            APIRiskFinding.endpoint_id == endpoint_id,
            APIRiskFinding.rule_name == rule_name,
        )
    ).first()

    if finding:
        finding.severity = severity
        finding.title = title
        finding.description = description
        finding.evidence = evidence or {}
        finding.status = status
        finding.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(finding)
        return finding

    finding = APIRiskFinding(
        project_id=project_id,
        endpoint_id=endpoint_id,
        rule_name=rule_name,
        severity=severity,
        title=title,
        description=description,
        evidence=evidence or {},
        status=status,
        status_history=[],
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


def get_api_risk_finding(db: Session, finding_id: UUID) -> Optional[APIRiskFinding]:
    return db.get(APIRiskFinding, finding_id)


def list_api_risk_findings(
    db: Session,
    project_id: UUID,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[APIRiskFinding]:
    stmt = select(APIRiskFinding).where(APIRiskFinding.project_id == project_id)
    if severity:
        stmt = stmt.where(APIRiskFinding.severity == severity)
    if status:
        stmt = stmt.where(APIRiskFinding.status == status)
    stmt = stmt.order_by(APIRiskFinding.updated_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_api_risk_findings(
    db: Session,
    project_id: UUID,
    severity: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    stmt = select(func.count()).select_from(APIRiskFinding).where(
        APIRiskFinding.project_id == project_id
    )
    if severity:
        stmt = stmt.where(APIRiskFinding.severity == severity)
    if status:
        stmt = stmt.where(APIRiskFinding.status == status)
    return db.scalar(stmt) or 0


def update_api_risk_status(
    db: Session,
    finding: APIRiskFinding,
    status: str,
    updated_by: str,
    resolution_notes: Optional[str] = None,
) -> APIRiskFinding:
    """Update API risk status and append status transition history."""
    previous_status = finding.status
    finding.status = status
    finding.updated_by = updated_by
    finding.resolution_notes = resolution_notes
    finding.updated_at = datetime.now(timezone.utc)

    if status in {"resolved", "false_positive"}:
        finding.resolved_at = datetime.now(timezone.utc)
    elif previous_status in {"resolved", "false_positive"} and status not in {
        "resolved",
        "false_positive",
    }:
        finding.resolved_at = None

    _append_status_history(
        finding=finding,
        previous_status=previous_status,
        new_status=status,
        updated_by=updated_by,
        notes=resolution_notes,
    )
    db.commit()
    db.refresh(finding)
    return finding
