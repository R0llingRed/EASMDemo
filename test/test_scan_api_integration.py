"""Real DB integration test for scan create/start -> API risks query."""

import os
from contextlib import contextmanager
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("psycopg")

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from server.app.api import api_risks as api_risks_api
from server.app.api import scans as scans_api
from server.app.crud import api_risk_finding as crud_api_risk
from server.app.crud import project as crud_project
from server.app.crud import scan_policy as crud_scan_policy
from shared.config import settings


def _to_sqlalchemy_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


def _to_psycopg_url(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+psycopg://", "postgresql://", 1)


@contextmanager
def _temporary_migrated_database():
    import psycopg

    raw_base_url = os.environ.get("EASM_DATABASE_URL")
    if not raw_base_url:
        pytest.skip("EASM_DATABASE_URL is required for DB integration tests")

    base_url = make_url(_to_sqlalchemy_url(raw_base_url))
    db_name = f"easm_test_{uuid4().hex[:8]}"

    admin_url: URL = base_url.set(database="postgres")
    test_url: URL = base_url.set(database=db_name)
    admin_psycopg_url = _to_psycopg_url(admin_url.render_as_string(hide_password=False))
    test_sqlalchemy_url = test_url.render_as_string(hide_password=False)

    old_database_url = settings.database_url
    try:
        with psycopg.connect(admin_psycopg_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f'CREATE DATABASE "{db_name}"')

        settings.database_url = test_sqlalchemy_url
        command.upgrade(Config("server/alembic.ini"), "head")
        yield test_sqlalchemy_url
    except Exception as exc:
        pytest.skip(f"Postgres integration setup unavailable: {exc}")
    finally:
        settings.database_url = old_database_url
        try:
            with psycopg.connect(admin_psycopg_url, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT pg_terminate_backend(pid) "
                        "FROM pg_stat_activity "
                        "WHERE datname = %s AND pid <> pg_backend_pid()",
                        (db_name,),
                    )
                    cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        except Exception:
            # Best-effort cleanup for local environments.
            pass


def test_scan_create_start_then_query_api_risks_real_db(monkeypatch):
    with _temporary_migrated_database() as db_url:
        engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        with SessionLocal() as db:
            project = crud_project.create_project(db=db, name=f"p-{uuid4().hex[:6]}", description=None)
            policy = crud_scan_policy.create_scan_policy(
                db=db,
                project_id=project.id,
                name="default",
                scan_config={"batch_size": 20},
                is_default=True,
                enabled=True,
            )
            project_id = project.id
            policy_id = policy.id

        app = FastAPI()
        app.include_router(scans_api.router)
        app.include_router(api_risks_api.router)

        def override_get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[scans_api.get_project_dep] = lambda: type("P", (), {"id": project_id})()
        app.dependency_overrides[scans_api.get_db] = override_get_db
        app.dependency_overrides[api_risks_api.get_project_dep] = lambda: type("P", (), {"id": project_id})()
        app.dependency_overrides[api_risks_api.get_db] = override_get_db

        def fake_dispatch(task):
            with SessionLocal() as db:
                crud_api_risk.create_or_update_api_risk_finding(
                    db=db,
                    project_id=task.project_id,
                    endpoint_id=None,
                    rule_name="sensitive_api_surface",
                    severity="high",
                    title="Sensitive endpoint in JS",
                    description="Detected /admin endpoint in JS assets",
                    evidence={"endpoint": "/admin/user", "method": "POST"},
                )

        monkeypatch.setattr(scans_api, "_dispatch_scan_task", fake_dispatch)

        client = TestClient(app)

        create_resp = client.post(
            f"/projects/{project_id}/scans",
            json={
                "task_type": "js_api_discovery",
                "policy_id": str(policy_id),
                "config": {"batch_size": 50},
                "priority": 8,
            },
        )
        assert create_resp.status_code == 201
        create_data = create_resp.json()
        assert create_data["scan_policy_id"] == str(policy_id)
        assert create_data["config"]["batch_size"] == 50
        assert create_data["priority"] == 8

        scan_id = create_data["id"]
        start_resp = client.post(f"/projects/{project_id}/scans/{scan_id}/start")
        assert start_resp.status_code == 200

        risks_resp = client.get(f"/projects/{project_id}/api-risks")
        assert risks_resp.status_code == 200
        risk_data = risks_resp.json()
        assert risk_data["total"] == 1
        assert risk_data["items"][0]["rule_name"] == "sensitive_api_surface"

        engine.dispose()
