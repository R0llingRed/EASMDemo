"""Vulnerability API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.api.deps import get_project_dep
from server.app.crud import vulnerability as crud_vuln
from server.app.db.session import get_db
from server.app.models.project import Project
from server.app.schemas.common import Page
from server.app.schemas.vulnerability import (
    VulnerabilityDetail,
    VulnerabilityOut,
    VulnerabilityStats,
    VulnerabilityUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/vulnerabilities", tags=["vulnerabilities"])


@router.get("", response_model=Page[VulnerabilityOut])
def list_vulnerabilities(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    template_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """List vulnerabilities for a project."""
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20

    vulns = crud_vuln.list_vulnerabilities(
        db=db,
        project_id=project.id,
        severity=severity,
        status=status,
        template_id=template_id,
        skip=skip,
        limit=limit,
    )
    total = crud_vuln.count_vulnerabilities(
        db=db,
        project_id=project.id,
        severity=severity,
        status=status,
        template_id=template_id,
    )
    return Page(items=vulns, total=total, skip=skip, limit=limit)


@router.get("/stats", response_model=VulnerabilityStats)
def get_vulnerability_stats(
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """Get vulnerability statistics for a project."""
    stats = crud_vuln.get_vulnerability_stats(db=db, project_id=project.id)
    return VulnerabilityStats(**stats)


@router.get("/{vuln_id}", response_model=VulnerabilityDetail)
def get_vulnerability(
    vuln_id: UUID,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """Get vulnerability details."""
    vuln = crud_vuln.get_vulnerability(db=db, vuln_id=vuln_id)
    if not vuln or vuln.project_id != project.id:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.patch("/{vuln_id}", response_model=VulnerabilityOut)
def update_vulnerability(
    vuln_id: UUID,
    body: VulnerabilityUpdate,
    project: Project = Depends(get_project_dep),
    db: Session = Depends(get_db),
):
    """Update vulnerability status."""
    vuln = crud_vuln.get_vulnerability(db=db, vuln_id=vuln_id)
    if not vuln or vuln.project_id != project.id:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    updated = crud_vuln.update_vulnerability(
        db=db,
        vuln_id=vuln_id,
        status=body.status.value if body.status else None,
        is_false_positive=body.is_false_positive,
    )
    return updated
