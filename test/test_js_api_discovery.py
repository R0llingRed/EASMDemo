"""Tests for JS deep discovery task."""

from types import SimpleNamespace
from uuid import uuid4

from worker.app.tasks import js_api_discovery


def test_run_js_api_discovery_discovers_scripts_endpoints_and_risks(monkeypatch):
    from server.app.crud import api_endpoint as crud_api_endpoint
    from server.app.crud import api_risk_finding as crud_api_risk
    from server.app.crud import js_asset as crud_js_asset
    from server.app.crud import web_asset as crud_web_asset

    project_id = uuid4()
    web_asset_id = uuid4()
    js_asset_id = uuid4()
    endpoint_id = uuid4()

    task = SimpleNamespace(
        project_id=project_id,
        config={"batch_size": 10, "max_scripts_per_page": 10},
    )
    assets = [SimpleNamespace(id=web_asset_id, url="https://example.com")]

    monkeypatch.setattr(
        crud_web_asset,
        "list_web_assets",
        lambda db, project_id, is_alive, limit: assets,
    )

    def fake_fetch(url: str, verify_tls: bool, max_size: int = 512000):
        if url == "https://example.com":
            return '<script src="/static/app.js"></script><script>fetch("/graphql")</script>'
        if url == "https://example.com/static/app.js":
            return 'axios.post("/admin/user", body)'
        return None

    monkeypatch.setattr(js_api_discovery, "_fetch_text", fake_fetch)

    monkeypatch.setattr(
        crud_js_asset,
        "upsert_js_asset",
        lambda **kwargs: SimpleNamespace(id=js_asset_id),
    )

    endpoints_seen = []

    def fake_upsert_api_endpoint(**kwargs):
        endpoints_seen.append((kwargs["method"], kwargs["endpoint"]))
        return SimpleNamespace(id=endpoint_id, endpoint=kwargs["endpoint"], method=kwargs["method"])

    monkeypatch.setattr(crud_api_endpoint, "upsert_api_endpoint", fake_upsert_api_endpoint)

    risk_seen = []

    def fake_upsert_risk(**kwargs):
        risk_seen.append((str(kwargs["endpoint_id"]), kwargs["rule_name"]))
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr(crud_api_risk, "create_or_update_api_risk_finding", fake_upsert_risk)

    result = js_api_discovery._run_js_api_discovery(db=None, task=task)

    assert result["pages_scanned"] == 1
    assert result["scripts_discovered"] == 2
    assert result["api_endpoints_discovered"] == 2
    assert result["api_risks_flagged"] == 3
    assert ("POST", "/admin/user") in endpoints_seen
    assert ("GET", "/graphql") in endpoints_seen
    assert ("insecure_transport" not in {name for _, name in risk_seen})
