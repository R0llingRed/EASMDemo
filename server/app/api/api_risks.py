"""API risk finding routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import api_risk_finding as crud_api_risk
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.js_api import APIRiskFindingOut, APIRiskStatusUpdate

router = APIRouter(prefix="/projects/{project_id}/api-risks", tags=["api-risks"])


@router.get("", response_model=Page[APIRiskFindingOut])
def list_project_api_risks(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 500:
        limit = 100

    items = crud_api_risk.list_api_risk_findings(
        db=db,
        project_id=project.id,
        severity=severity,
        status=status,
        skip=skip,
        limit=limit,
    )
    total = crud_api_risk.count_api_risk_findings(
        db=db,
        project_id=project.id,
        severity=severity,
        status=status,
    )
    return Page(items=items, total=total)


@router.get("/{finding_id}", response_model=APIRiskFindingOut)
def get_project_api_risk(
    finding_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    finding = crud_api_risk.get_api_risk_finding(db=db, finding_id=finding_id)
    if not finding or finding.project_id != project.id:
        raise HTTPException(status_code=404, detail="API risk finding not found")
    return finding


@router.patch("/{finding_id}/status", response_model=APIRiskFindingOut)
def update_project_api_risk_status(
    finding_id: UUID,
    body: APIRiskStatusUpdate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """Update API risk status with audit metadata."""
    finding = crud_api_risk.get_api_risk_finding(db=db, finding_id=finding_id)
    if not finding or finding.project_id != project.id:
        raise HTTPException(status_code=404, detail="API risk finding not found")

    status_value = body.status.value
    if status_value in {"resolved", "false_positive"} and not body.resolution_notes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="resolution_notes is required for resolved/false_positive status",
        )

    updated = crud_api_risk.update_api_risk_status(
        db=db,
        finding=finding,
        status=status_value,
        updated_by=body.updated_by,
        resolution_notes=body.resolution_notes,
    )
    return updated
