from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from server.app.crud.project import get_project
from server.app.models.project import Project
from shared.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db():
    from server.app.db.session import get_db as _get_db

    yield from _get_db()


def require_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """Require API key authentication when enabled."""
    if not settings.auth_enabled:
        return "auth-disabled"

    allowed_keys = settings.get_allowed_api_keys()
    if not api_key or api_key not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing api key",
        )
    return api_key


def _is_project_access_allowed(api_key: str, project_id: UUID) -> bool:
    """Validate project-level access from API key ACL."""
    if not settings.auth_enabled:
        return True

    acl = settings.get_api_key_project_acl()
    if not acl:
        return True

    allowed_projects = acl.get(api_key)
    if not allowed_projects:
        return False

    project_id_str = str(project_id)
    return "*" in allowed_projects or project_id_str in allowed_projects


def get_project_dep(
    project_id: UUID,
    api_key: str = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> Project:
    if not _is_project_access_allowed(api_key, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="api key has no access to this project",
        )

    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    return project
